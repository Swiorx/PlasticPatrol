import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

const API_BASE = 'http://localhost:8000';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  let url = req.url;
  if (url.startsWith('/api/')) {
    url = API_BASE + url;
  }

  const token = auth.token();
  const cloned = req.clone({
    url,
    setHeaders: token ? { Authorization: `Bearer ${token}` } : {},
  });

  return next(cloned).pipe(
    catchError((err: HttpErrorResponse) => {
      if (err.status === 401) {
        auth.logout();
        router.navigate(['/login']);
      }
      return throwError(() => err);
    })
  );
};
