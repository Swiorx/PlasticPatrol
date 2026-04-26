import { Component, AfterViewInit, OnDestroy, PLATFORM_ID, Inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { ApiService, DebrisOut } from '../../services/api.service';
import { CollectOverlayComponent } from '../collect-overlay/collect-overlay';
import { Header } from '../header/header';

const RADIUS_KM = 12;
const POST_LOCATION_MIN_INTERVAL_MS = 30_000;
const POST_LOCATION_MIN_DISTANCE_M = 50;
const COLLECT_RADIUS_M = 100;

@Component({
  selector: 'app-map',
  standalone: true,
  imports: [CommonModule, CollectOverlayComponent, Header],
  templateUrl: './map.html',
  styleUrl: './map.scss'
})
export class Map implements AfterViewInit, OnDestroy {
  latitude: number | null = null;
  longitude: number | null = null;
  errorMsg: string | null = null;
  statusMsg: string | null = null;
  refreshing = false;
  debrisCount = 0;

  showCollectOverlay = false;
  activeReservationId: number | null = null;
  activeClusterEcoPoints = 0;

  private map: any;
  private userMarker: any;
  private debrisLayer: any;
  private L: any;
  private watchId: number | null = null;
  private debris: DebrisOut[] = [];

  private lastPostedAt = 0;
  private lastPostedLat: number | null = null;
  private lastPostedLon: number | null = null;
  private debrisLoaded = false;
  private hasCentered = false;

  constructor(
    @Inject(PLATFORM_ID) private platformId: Object,
    private cdr: ChangeDetectorRef,
    private api: ApiService
  ) { }

  async ngAfterViewInit() {
    if (!isPlatformBrowser(this.platformId)) return;

    const L = await import('leaflet');
    this.L = L;

    this.map = L.map('map-container').setView([51.505, -0.09], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(this.map);

    this.debrisLayer = L.layerGroup().addTo(this.map);

    if ('geolocation' in navigator) {
      // 1) Fast low-accuracy fix so the UI updates within ~1s
      navigator.geolocation.getCurrentPosition(
        (pos) => this.onPosition(pos),
        (err) => this.handleGeoError(err),
        { enableHighAccuracy: false, timeout: 5000, maximumAge: 60000 }
      );

      // 2) Live high-accuracy updates after that
      this.watchId = navigator.geolocation.watchPosition(
        (pos) => this.onPosition(pos),
        (err) => this.handleGeoError(err),
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 3000 }
      );
    } else {
      this.errorMsg = 'Geolocation is not supported by your browser.';
      this.cdr.detectChanges();
    }
  }

  private onPosition(position: GeolocationPosition) {
    const lat = position.coords.latitude;
    const lon = position.coords.longitude;
    this.latitude = lat;
    this.longitude = lon;
    this.errorMsg = null;

    if (!this.hasCentered) {
      this.map.setView([lat, lon], 13);
      this.hasCentered = true;
    }

    if (!this.userMarker) {
      const icon = this.L.icon({
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
        iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41]
      });
      this.userMarker = this.L.marker([lat, lon], { icon }).addTo(this.map);
    } else {
      this.userMarker.setLatLng([lat, lon]);
    }

    this.maybePostLocation(lat, lon);

    if (!this.debrisLoaded) {
      this.debrisLoaded = true;
      this.loadDebris();
    } else {
      this.renderDebris(this.debris);
    }

    this.cdr.detectChanges();
  }

  private maybePostLocation(lat: number, lon: number) {
    const now = Date.now();
    const movedFar =
      this.lastPostedLat === null || this.lastPostedLon === null ||
      this.haversineMeters(this.lastPostedLat, this.lastPostedLon, lat, lon) > POST_LOCATION_MIN_DISTANCE_M;

    if (now - this.lastPostedAt < POST_LOCATION_MIN_INTERVAL_MS && !movedFar) return;
    this.lastPostedAt = now;
    this.lastPostedLat = lat;
    this.lastPostedLon = lon;

    this.api.postLocation(lat, lon).subscribe({ error: (err: HttpErrorResponse) => console.warn('postLocation failed', err) });
  }

  private handleGeoError(err: GeolocationPositionError) {
    // Don't overwrite a good fix with a transient watchPosition timeout
    if (this.latitude !== null && this.longitude !== null && err.code === err.TIMEOUT) return;

    this.errorMsg =
      err.code === err.PERMISSION_DENIED
        ? 'Location permission denied. Click the location icon in the address bar and allow access, then refresh.'
        : err.code === err.POSITION_UNAVAILABLE
          ? 'Could not determine your location. Check that location services are enabled on your device.'
          : err.code === err.TIMEOUT
            ? 'Locating is taking too long. Try moving outside or refreshing.'
            : `Geolocation error: ${err.message}`;
    this.cdr.detectChanges();
  }

  loadDebris() {
    this.api.getDebris(RADIUS_KM).subscribe({
      next: (items) => { this.debris = items; this.renderDebris(items); },
      error: (err: HttpErrorResponse) => {
        if (err.status !== 401) {
          this.statusMsg = err.error?.detail || 'Could not load debris';
          this.cdr.detectChanges();
        }
      }
    });
  }

  refreshSatellite() {
    if (this.refreshing || this.latitude === null || this.longitude === null) return;
    this.refreshing = true;
    this.statusMsg = 'Scanning satellite imagery...';
    this.cdr.detectChanges();

    this.api.refreshSatellite(RADIUS_KM).subscribe({
      next: (res) => {
        this.refreshing = false;
        this.statusMsg = `Scan complete: ${res.inserted} new debris.`;
        this.loadDebris();
        this.cdr.detectChanges();
      },
      error: (err: HttpErrorResponse) => {
        this.refreshing = false;
        this.statusMsg = `Scan failed: ${err.error?.detail || err.message}`;
        this.cdr.detectChanges();
      }
    });
  }

  private renderDebris(items: DebrisOut[]) {
    this.debrisLayer.clearLayers();

    for (const d of items) {
      const color = d.is_reserved
        ? '#f59e0b'
        : d.size_category === 'large' ? '#ef4444'
          : d.size_category === 'medium' ? '#f97316'
            : '#3b82f6';

      const icon = this.L.divIcon({
        className: '',
        html: `<div style="width:14px;height:14px;border-radius:50%;background:${color};border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,0.4)"></div>`,
        iconSize: [14, 14],
        iconAnchor: [7, 7],
      });

      const nearEnough = this.latitude !== null && this.longitude !== null &&
        this.haversineMeters(this.latitude, this.longitude, d.latitude, d.longitude) <= COLLECT_RADIUS_M;

      let popupHtml = `<div class="custom-popup">
        <div class="cluster-title">${d.size_category} cluster</div>
        <div class="cluster-info">${d.source_point_count} point(s)</div>
        <div class="cluster-eco">${d.eco_points} eco points</div>
        <div class="cluster-coords">${d.latitude.toFixed(4)}, ${d.longitude.toFixed(4)}</div>`;

      if (d.is_reserved && d.reservation_id !== null) {
        const disabled = nearEnough ? '' : 'disabled';
        const title = nearEnough ? '' : 'title="Get within 100m to collect"';
        popupHtml += `<button class="btn-primary" ${disabled} ${title} onclick="window._collectCluster(${d.reservation_id}, ${d.eco_points})">Collect</button></div>`;
      } else {
        popupHtml += `<button class="btn-accent" onclick="window._reserveCluster(${JSON.stringify(d.source_point_ids)}, ${d.latitude}, ${d.longitude}, ${d.eco_points})">Reserve</button></div>`;
      }

      this.L.marker([d.latitude, d.longitude], { icon })
        .bindPopup(popupHtml)
        .addTo(this.debrisLayer);
    }

    (window as any)._reserveCluster = (pointIds: number[], lat: number, lon: number, eco: number) => {
      this.onReserve(pointIds, lat, lon, eco);
    };
    (window as any)._collectCluster = (reservationId: number, eco: number) => {
      this.onCollect(reservationId, eco);
    };

    this.debrisCount = items.length;
    this.cdr.detectChanges();
  }

  onReserve(pointIds: number[], centerLat: number, centerLon: number, ecoPoints: number) {
    this.api.reserveCluster(pointIds, centerLat, centerLon, ecoPoints).subscribe({
      next: () => {
        this.statusMsg = 'Reserved! You have 24h to collect.';
        this.loadDebris();
      },
      error: (err: HttpErrorResponse) => {
        const msg = err.error?.detail || 'Could not reserve';
        this.statusMsg = msg;
        alert(msg); // Alert the user directly
        this.loadDebris(); // Refresh to hide the debris since it's reserved by someone else
        this.cdr.detectChanges();
      }
    });
  }

  onCollect(reservationId: number, ecoPoints: number) {
    this.activeReservationId = reservationId;
    this.activeClusterEcoPoints = ecoPoints;
    this.showCollectOverlay = true;
    this.cdr.detectChanges();
  }

  onOverlayClosed() {
    this.showCollectOverlay = false;
    this.activeReservationId = null;
    this.cdr.detectChanges();
  }

  onOverlayCollected() {
    this.showCollectOverlay = false;
    this.activeReservationId = null;
    this.loadDebris();
    this.cdr.detectChanges();
  }

  private haversineMeters(lat1: number, lon1: number, lat2: number, lon2: number): number {
    const R = 6371000;
    const toRad = (d: number) => d * Math.PI / 180;
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(a));
  }

  ngOnDestroy() {
    if (isPlatformBrowser(this.platformId)) {
      if (this.watchId !== null) navigator.geolocation.clearWatch(this.watchId);
      if (this.map) this.map.remove();
      delete (window as any)._reserveCluster;
      delete (window as any)._collectCluster;
    }
  }
}