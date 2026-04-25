import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

export interface StatsResponse {
  total_detected: number;
  total_collected: number;
  total_verified: number;
  total_pending_verification: number;
  collection_rate_percent: number;
  total_users: number;
  total_eco_points_awarded: number;
}

@Injectable({ providedIn: 'root' })
export class StatsService {
  private http = inject(HttpClient);

  getStats() {
    return this.http.get<StatsResponse>('http://localhost:8000/api/stats/');
  }
}
