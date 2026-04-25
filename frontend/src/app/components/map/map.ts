import { Component, OnInit, OnDestroy, NgZone, Inject, PLATFORM_ID, AfterViewInit, ChangeDetectorRef } from '@angular/core';
import { isPlatformBrowser, DecimalPipe } from '@angular/common';

@Component({
  selector: 'app-map',
  imports: [DecimalPipe],
  templateUrl: './map.html',
  styleUrl: './map.scss',
})
export class Map implements OnInit, OnDestroy, AfterViewInit {
  public lat: number | undefined;
  public lng: number | undefined;
  public errorMsg: string = '';
  private map: any;
  private userMarker: any;
  private L: any;

  constructor(
    private ngZone: NgZone,
    @Inject(PLATFORM_ID) private platformId: Object,
    private cdr: ChangeDetectorRef
  ) { }

  public ngOnInit(): void {
  }

  public ngAfterViewInit(): void {
    if (isPlatformBrowser(this.platformId)) {
      this.initMap();
    }
  }

  public ngOnDestroy(): void {
    if (this.map) {
      this.map.stopLocate();
      this.map.remove();
    }
  }

  private async initMap() {
    this.L = await import('leaflet');

    this.map = this.L.map('map-container', {
      zoomControl: false
    }).setView([0, 0], 2);

    this.L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(this.map);

    // Track the center of the map in real-time
    this.map.on('move', () => {
      this.ngZone.run(() => {
        const center = this.map.getCenter();
        this.lat = center.lat;
        this.lng = center.lng;
        this.errorMsg = ''; // Clear error once we have coordinates
        this.cdr.detectChanges();
      });
    });

    // Handle Leaflet's built-in location finding
    this.map.on('locationfound', (e: any) => {
      this.ngZone.run(() => {
        this.errorMsg = '';

        if (!this.userMarker) {
          this.userMarker = this.L.circleMarker(e.latlng, {
            radius: 8,
            fillColor: "#2b5cff",
            color: "#fff",
            weight: 3,
            opacity: 1,
            fillOpacity: 0.8
          }).addTo(this.map);
        } else {
          this.userMarker.setLatLng(e.latlng);
        }
        this.cdr.detectChanges();
      });
    });

    this.map.on('locationerror', (e: any) => {
      this.ngZone.run(() => {
        if (!this.userMarker) {
          this.errorMsg = `Location error: ${e.message}`;
        }
        this.cdr.detectChanges();
      });
    });

    this.errorMsg = 'Fetching location...';

    // Start tracking user location automatically
    this.map.locate({
      setView: true,
      maxZoom: 16,
      watch: true,
      enableHighAccuracy: true
    });
  }
}