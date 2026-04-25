import { Component, OnInit, OnDestroy, PLATFORM_ID, Inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { ApiService, DebrisOut } from '../../services/api.service';

const RADIUS_KM = 12;
const POST_LOCATION_MIN_INTERVAL_MS = 30_000;
const POST_LOCATION_MIN_DISTANCE_M = 50;

@Component({
  selector: 'app-map',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './map.html',
  styleUrl: './map.scss'
})
export class Map implements OnInit, OnDestroy {
  latitude: number | null = null;
  longitude: number | null = null;
  errorMsg: string | null = null;
  statusMsg: string | null = null;
  refreshing = false;
  debrisCount = 0;

  private map: any;
  private marker: any;
  private debrisLayer: any;
  private L: any;
  private watchId: number | null = null;

  private lastPostedAt = 0;
  private lastPostedLat: number | null = null;
  private lastPostedLon: number | null = null;
  private debrisLoaded = false;

  constructor(
    @Inject(PLATFORM_ID) private platformId: Object,
    private cdr: ChangeDetectorRef,
    private api: ApiService
  ) {}

  async ngOnInit() {
    if (!isPlatformBrowser(this.platformId)) return;

    const L = await import('leaflet');
    this.L = L;

    this.map = L.map('map-container').setView([51.505, -0.09], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(this.map);

    this.debrisLayer = L.layerGroup().addTo(this.map);

    if ('geolocation' in navigator) {
      this.watchId = navigator.geolocation.watchPosition(
        (position) => this.onPosition(position),
        (error) => {
          this.errorMsg = `Geolocation error: ${error.message}`;
          this.cdr.detectChanges();
        },
        { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
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

    const latlng: [number, number] = [lat, lon];
    this.map.setView(latlng, 13);

    if (!this.marker) {
      const icon = this.L.icon({
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
      });
      this.marker = this.L.marker(latlng, { icon }).addTo(this.map);
    } else {
      this.marker.setLatLng(latlng);
    }

    this.maybePostLocation(lat, lon);

    if (!this.debrisLoaded) {
      this.debrisLoaded = true;
      this.loadDebris();
    }

    this.cdr.detectChanges();
  }

  private maybePostLocation(lat: number, lon: number) {
    const now = Date.now();
    const movedFar =
      this.lastPostedLat === null ||
      this.lastPostedLon === null ||
      this.haversineMeters(this.lastPostedLat, this.lastPostedLon, lat, lon) > POST_LOCATION_MIN_DISTANCE_M;

    if (now - this.lastPostedAt < POST_LOCATION_MIN_INTERVAL_MS && !movedFar) return;

    this.lastPostedAt = now;
    this.lastPostedLat = lat;
    this.lastPostedLon = lon;

    this.api.postLocation(lat, lon).subscribe({
      error: (err: HttpErrorResponse) => {
        console.warn('postLocation failed', err);
      }
    });
  }

  loadDebris() {
    this.api.getDebris(RADIUS_KM).subscribe({
      next: (items) => this.renderDebris(items),
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
    const debrisIcon = this.L.divIcon({
      className: 'debris-dot',
      iconSize: [12, 12],
      iconAnchor: [6, 6],
    });
    for (const d of items) {
      this.L.marker([d.latitude, d.longitude], { icon: debrisIcon })
        .bindPopup(
          `Debris #${d.id}<br>${d.size_category}<br>` +
          (d.is_collected ? 'Collected' : 'Not collected') +
          (d.is_verified ? ' (verified)' : '')
        )
        .addTo(this.debrisLayer);
    }
    this.debrisCount = items.length;
    this.cdr.detectChanges();
  }

  private haversineMeters(lat1: number, lon1: number, lat2: number, lon2: number): number {
    const R = 6371000;
    const toRad = (d: number) => d * Math.PI / 180;
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a = Math.sin(dLat / 2) ** 2 +
              Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(a));
  }

  ngOnDestroy() {
    if (isPlatformBrowser(this.platformId)) {
      if (this.watchId !== null) {
        navigator.geolocation.clearWatch(this.watchId);
      }
      if (this.map) {
        this.map.remove();
      }
    }
  }
}
