import { CanActivateFn } from '@angular/router';
import { adminRoleGuard } from './admin-role.guard';

export const roleGuard: CanActivateFn = adminRoleGuard;
export { adminRoleGuard };
