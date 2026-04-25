import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { UserOut } from './auth.service';

export interface DebrisOut {
  id: number;
  latitude: number;
  longitude: number;
  size_category: string;
  is_collected: boolean;
  is_verified: boolean;
  eco_points: number;
}

export interface RefreshResult {
  inserted: number;
  scanned_points: number;
  bbox: number[];
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  constructor(private http: HttpClient) {}

  postLocation(lat: number, lon: number): Observable<UserOut> {
    return this.http.post<UserOut>('/api/users/me/location', {
      latitude: lat,
      longitude: lon,
    });
  }

  getDebris(radiusKm: number = 12): Observable<DebrisOut[]> {
    const params = new HttpParams().set('radius_km', radiusKm.toString());
    return this.http.get<DebrisOut[]>('/api/users/me/debris', { params });
  }

  refreshSatellite(radiusKm: number = 12): Observable<RefreshResult> {
    const params = new HttpParams().set('radius_km', radiusKm.toString());
    return this.http.post<RefreshResult>('/api/users/me/refresh-satellite', null, { params });
  }
}
