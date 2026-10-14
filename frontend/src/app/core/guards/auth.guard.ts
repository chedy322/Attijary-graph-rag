import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { from, map, catchError, of, switchMap } from 'rxjs';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  return from(authService.initialize()).pipe(
    map(() =>
      authService.isAuthenticated()
        ? true
        : router.createUrlTree(['/sign-in'], {
            queryParams: { returnUrl: state.url },
          }),
    ),
    catchError(() =>
      of(
        router.createUrlTree(['/sign-in'], {
          queryParams: { returnUrl: state.url },
        }),
      ),
    ),
  );
};
