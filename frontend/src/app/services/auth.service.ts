import { Injectable, Inject, PLATFORM_ID, signal } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

export interface UserOut {
  id: number;
  username: string;
  email: string;
  eco_points: number;
  is_active: boolean;
  is_authorized: boolean;
  latitude: number | null;
  longitude: number | null;
}

export interface TokenOut {
  access_token: string;
  token_type: string;
  user: UserOut;
}

const TOKEN_KEY = 'pp_token';
const USER_KEY = 'pp_user';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly browser: boolean;
  readonly currentUser = signal<UserOut | null>(null);

  constructor(
    private http: HttpClient,
    @Inject(PLATFORM_ID) platformId: Object
  ) {
    this.browser = isPlatformBrowser(platformId);
    if (this.browser) {
      const raw = localStorage.getItem(USER_KEY);
      if (raw) {
        try { this.currentUser.set(JSON.parse(raw)); } catch { /* ignore */ }
      }
    }
  }

  token(): string | null {
    if (!this.browser) return null;
    return localStorage.getItem(TOKEN_KEY);
  }

  isLoggedIn(): boolean {
    return this.token() !== null;
  }

  login(usernameOrEmail: string, password: string): Observable<TokenOut> {
    const body = new HttpParams()
      .set('username', usernameOrEmail)
      .set('password', password);
    return this.http
      .post<TokenOut>('/api/users/login', body.toString(), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      .pipe(tap((res) => this.persist(res)));
  }

  register(username: string, email: string, password: string): Observable<TokenOut> {
    return this.http
      .post<TokenOut>('/api/users/register', { username, email, password })
      .pipe(tap((res) => this.persist(res)));
  }

  logout(): void {
    if (this.browser) {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    }
    this.currentUser.set(null);
  }

  setUser(user: UserOut): void {
    this.currentUser.set(user);
    if (this.browser) localStorage.setItem(USER_KEY, JSON.stringify(user));
  }

  private persist(res: TokenOut): void {
    if (this.browser) {
      localStorage.setItem(TOKEN_KEY, res.access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(res.user));
    }
    this.currentUser.set(res.user);
  }
}
