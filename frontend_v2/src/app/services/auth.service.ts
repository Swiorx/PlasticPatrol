import { Injectable, inject, signal, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { tap } from 'rxjs/operators';

const TOKEN_KEY = 'pp_token';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private platformId = inject(PLATFORM_ID);
  private isBrowser = isPlatformBrowser(this.platformId);

  isLoggedIn = signal(this.isBrowser ? !!localStorage.getItem(TOKEN_KEY) : false);

  getToken(): string | null {
    return this.isBrowser ? localStorage.getItem(TOKEN_KEY) : null;
  }

  login(email: string, password: string) {
    const body = new URLSearchParams({ username: email, password });
    return this.http.post<{ access_token: string }>(
      'http://localhost:8000/api/auth/token',
      body.toString(),
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    ).pipe(tap(res => {
      if (this.isBrowser) {
        localStorage.setItem(TOKEN_KEY, res.access_token);
      }
      this.isLoggedIn.set(true);
    }));
  }

  register(username: string, email: string, password: string) {
    return this.http.post('http://localhost:8000/api/auth/register', { username, email, password });
  }

  logout() {
    if (this.isBrowser) {
      localStorage.removeItem(TOKEN_KEY);
    }
    this.isLoggedIn.set(false);
  }
}
