import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { UserOut } from './auth.service';

export interface DebrisOut {
  id: string;
  latitude: number;
  longitude: number;
  size_category: string;
  is_collected: boolean;
  is_verified: boolean;
  eco_points: number;
  source_point_ids: number[];
  source_point_count: number;
  radius_m: number;
  is_reserved: boolean;
  reservation_id: number | null;
}

export interface RefreshResult {
  inserted: number;
  scanned_points: number;
  bbox: number[];
}

export interface ReservationOut {
  reservation_id: number;
  point_ids: number[];
  cluster_center_lat: number;
  cluster_center_lon: number;
  eco_points: number;
  reserved_until: string;
  status: string;
}

export interface CollectResult {
  message: string;
  eco_points_pending: number;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  constructor(private http: HttpClient) {}

  postLocation(lat: number, lon: number): Observable<UserOut> {
    return this.http.post<UserOut>('/api/users/me/location', { latitude: lat, longitude: lon });
  }

  getDebris(radiusKm: number = 12): Observable<DebrisOut[]> {
    const params = new HttpParams().set('radius_km', radiusKm.toString());
    return this.http.get<DebrisOut[]>('/api/users/me/debris', { params });
  }

  refreshSatellite(radiusKm: number = 12): Observable<RefreshResult> {
    const params = new HttpParams().set('radius_km', radiusKm.toString());
    return this.http.post<RefreshResult>('/api/users/me/refresh-satellite', null, { params });
  }

  reserveCluster(
    pointIds: number[],
    centerLat: number,
    centerLon: number,
    ecoPoints: number
  ): Observable<ReservationOut> {
    return this.http.post<ReservationOut>('/api/clusters/reserve', {
      point_ids: pointIds,
      center_lat: centerLat,
      center_lon: centerLon,
      eco_points: ecoPoints,
    });
  }

  collectCluster(reservationId: number, photo: File): Observable<CollectResult> {
    const formData = new FormData();
    formData.append('file', photo);
    return this.http.post<CollectResult>(`/api/clusters/${reservationId}/collect`, formData);
  }

  releaseReservation(reservationId: number): Observable<void> {
    return this.http.delete<void>(`/api/clusters/${reservationId}/reserve`);
  }

  getReservations(): Observable<ReservationOut[]> {
    return this.http.get<ReservationOut[]>('/api/users/me/reservations');
  }
}
