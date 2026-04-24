import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

export interface DebrisPoint {
  id: number;
  coordinates: string; // "POINT(lon lat)"
  size_category: string;
  detected_at: string;
  is_collected: boolean;
  eco_points: number;
}

@Injectable({ providedIn: 'root' })
export class PlasticService {
  constructor(private http: HttpClient) {}

  getAll() {
    return this.http.get<DebrisPoint[]>('http://localhost:8000/api/plastics/');
  }
}
