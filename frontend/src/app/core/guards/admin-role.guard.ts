import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

export const adminRoleGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (!authService.isAuthenticated()) {
    return router.createUrlTree(['/sign-in']);
  }

  if (authService.isAdmin()) {
    return true;
  }

  return router.createUrlTree(['/chat']);
};

export const roleGuard = adminRoleGuard;
