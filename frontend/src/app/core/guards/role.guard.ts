import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

export const roleGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (!authService.isLoggedIn()) {
    return router.createUrlTree(['/auth']);
  }

  if (authService.isAdmin()) {
    return true;
  }

  // Redirect standard users to /chat if unauthorized for admin routes
  return router.createUrlTree(['/chat']);
};
