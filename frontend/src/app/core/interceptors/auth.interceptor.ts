import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { from, of, switchMap, catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';
import { ApiErrorService } from '../services/api-error.service';
import { environment } from '../../../environments/environment';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const apiErrorService = inject(ApiErrorService);
  const router = inject(Router);

  const isBackendReq = req.url.startsWith(environment.apiUrl);

  if (!isBackendReq) {
    return next(req);
  }

  return from(authService.getClerkToken()).pipe(
    switchMap((token) => {
      const headers: Record<string, string> = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const authReq = req.clone({ setHeaders: headers });
      return next(authReq);
    }),
    catchError((error: HttpErrorResponse) => {
      apiErrorService.show(error);
      if (error.status === 401) {
        authService.logout();
        router.navigate(['/auth']);
      }
      return throwError(() => error);
    })
  );
};