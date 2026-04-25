import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { AuthService } from './auth.service';

export interface Notification {
  id: number;
  message: string;
  is_read: boolean;
  created_at: string;
}

@Injectable({ providedIn: 'root' })
export class NotificationsService {
  private http = inject(HttpClient);
  private auth = inject(AuthService);

  private headers() {
    return { headers: new HttpHeaders({ Authorization: `Bearer ${this.auth.getToken() ?? ''}` }) };
  }

  getAll() {
    return this.http.get<Notification[]>('http://localhost:8000/api/notifications/', this.headers());
  }

  getUnreadCount() {
    return this.http.get<{ unread_count: number }>('http://localhost:8000/api/notifications/unread/count', this.headers());
  }

  markAllRead() {
    return this.http.post('http://localhost:8000/api/notifications/read-all', {}, this.headers());
  }
}
