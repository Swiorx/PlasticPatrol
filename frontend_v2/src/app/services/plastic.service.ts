import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

export interface DebrisPoint {
  id: number;
  coordinates: string;
  size_category: string;
  is_verified: boolean;
  is_collected: boolean;
  eco_points: number;
  detected_at: string;
}

@Injectable({ providedIn: 'root' })
export class PlasticService {
  private http = inject(HttpClient);

  getAll() {
    return this.http.get<DebrisPoint[]>('http://localhost:8000/api/plastics/');
  }
}
