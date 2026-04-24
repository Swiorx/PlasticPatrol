import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { tap } from 'rxjs';

const API = 'http://localhost:8000/api/users';
const TOKEN_KEY = 'pp_token';

@Injectable({ providedIn: 'root' })
export class AuthService {
  readonly isLoggedIn = signal(!!localStorage.getItem(TOKEN_KEY));

  constructor(private http: HttpClient) {}

  register(username: string, email: string, password: string) {
    return this.http.post(`${API}/register`, { username, email, password });
  }

  login(email: string, password: string) {
    const body = new URLSearchParams({ username: email, password });
    return this.http.post<{ access_token: string }>(`${API}/login`, body.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }).pipe(tap(res => {
      localStorage.setItem(TOKEN_KEY, res.access_token);
      this.isLoggedIn.set(true);
    }));
  }

  logout() {
    localStorage.removeItem(TOKEN_KEY);
    this.isLoggedIn.set(false);
  }

  getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }
}
