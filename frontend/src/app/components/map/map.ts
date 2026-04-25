import { Component, OnInit, OnDestroy, PLATFORM_ID, Inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';

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

  private map: any;
  private marker: any;
  private watchId: number | null = null;

  constructor(
    @Inject(PLATFORM_ID) private platformId: Object,
    private cdr: ChangeDetectorRef
  ) {}

  async ngOnInit() {
    if (isPlatformBrowser(this.platformId)) {
      const L = await import('leaflet');

      // Initialize map with a default view
      this.map = L.map('map-container').setView([51.505, -0.09], 13);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
      }).addTo(this.map);

      // Start watching position
      if ('geolocation' in navigator) {
        this.watchId = navigator.geolocation.watchPosition(
          (position) => {
            this.latitude = position.coords.latitude;
            this.longitude = position.coords.longitude;
            this.errorMsg = null;

            const latlng: [number, number] = [this.latitude, this.longitude];

            // Update map view
            this.map.setView(latlng, 15);

            // Add or update marker
            if (!this.marker) {
              const icon = L.icon({
                iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
                iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
                shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41]
              });
              
              this.marker = L.marker(latlng, { icon }).addTo(this.map);
            } else {
              this.marker.setLatLng(latlng);
            }

            // Force change detection to update UI
            this.cdr.detectChanges();
          },
          (error) => {
            this.errorMsg = `Geolocation error: ${error.message}`;
            this.cdr.detectChanges();
          },
          {
            enableHighAccuracy: true,
            timeout: 5000,
            maximumAge: 0
          }
        );
      } else {
        this.errorMsg = 'Geolocation is not supported by your browser.';
        this.cdr.detectChanges();
      }
    }
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
