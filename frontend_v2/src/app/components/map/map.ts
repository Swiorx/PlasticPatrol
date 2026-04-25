import { Component, OnInit, OnDestroy, inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { PlasticService, DebrisPoint } from '../../services/plastic.service';

@Component({
  selector: 'app-map',
  imports: [],
  templateUrl: './map.html',
  styleUrl: './map.scss',
})
export class MapComponent implements OnInit, OnDestroy {
  private plasticService = inject(PlasticService);
  private platformId = inject(PLATFORM_ID);
  private map: any;

  debrisCount = 0;
  loading = true;
  error = '';

  ngOnInit() {
    if (isPlatformBrowser(this.platformId)) {
      this.initMap();
    }
  }

  private async initMap() {
    const L = await import('leaflet');

    this.map = L.map('pp-map', { zoomControl: true }).setView([20, 0], 3);

    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      { attribution: 'Tiles &copy; Esri &mdash; Source: Esri, USGS, NOAA', maxZoom: 18 }
    ).addTo(this.map);

    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
      { attribution: '', maxZoom: 18, opacity: 0.7 }
    ).addTo(this.map);

    this.loadDebris(L);
  }

  private loadDebris(L: any) {
    this.plasticService.getAll().subscribe({
      next: (points: DebrisPoint[]) => {
        this.debrisCount = points.length;
        this.loading = false;
        points.forEach((p: DebrisPoint) => this.addMarker(L, p));
      },
      error: () => {
        this.loading = false;
        this.error = 'Could not load debris data — is the backend running?';
      }
    });
  }

  private addMarker(L: any, p: DebrisPoint) {
    const match = p.coordinates?.match(/POINT\(([^ ]+) ([^ )]+)\)/);
    if (!match) return;
    const lon = parseFloat(match[1]);
    const lat = parseFloat(match[2]);

    const color = p.size_category === 'large' ? '#ef4444'
                : p.size_category === 'medium' ? '#f97316'
                : p.size_category === 'beach' ? '#a855f7'
                : '#eab308';

    const icon = L.divIcon({
      className: '',
      html: `<div style="width:10px;height:10px;background:${color};border:2px solid white;border-radius:50%;box-shadow:0 0 6px ${color}88"></div>`,
      iconSize: [10, 10],
      iconAnchor: [5, 5],
    });

    const verified = p.is_verified ? '✅ Verified' : '⏳ Pending';
    const collected = p.is_collected ? '✔ Collected' : 'Not collected';

    L.marker([lat, lon], { icon })
      .bindPopup(`
        <div style="font-family:monospace;font-size:12px;color:#e6edf3;background:#161b22;padding:12px 14px;border-radius:6px;min-width:170px;border:1px solid #30363d">
          <b style="color:#58a6ff">Debris #${p.id}</b><br><br>
          <span style="color:#8b949e">Size:</span> ${p.size_category ?? 'unknown'}<br>
          <span style="color:#8b949e">Status:</span> ${collected}<br>
          <span style="color:#8b949e">Verified:</span> ${verified}<br>
          <span style="color:#8b949e">Eco pts:</span> ${p.eco_points ?? 0}<br>
          <span style="color:#8b949e">Detected:</span> ${p.detected_at ? new Date(p.detected_at).toLocaleDateString() : 'N/A'}
        </div>
      `, { className: 'pp-popup' })
      .addTo(this.map);
  }

  ngOnDestroy() {
    this.map?.remove();
  }
}
