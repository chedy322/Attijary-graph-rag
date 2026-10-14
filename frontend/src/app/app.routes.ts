import { Routes } from '@angular/router';
import { AuthComponent } from './features/auth/auth.component';
import { AdminDashboardComponent } from './features/admin-dashboard/admin-dashboard.component';
import { ChatInterfaceComponent } from './features/chat-interface/chat-interface.component';
import { DocumentVerificationComponent } from './features/document-verification/document-verification.component';
import { GraphExplorerComponent } from './features/graph-explorer/graph-explorer.component';
import { AuditLogsComponent } from './features/audit-logs/audit-logs.component';
import { authGuard } from './core/guards/auth.guard';
import { adminRoleGuard } from './core/guards/admin-role.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'chat', pathMatch: 'full' },
  { path: 'auth', component: AuthComponent },
  { path: 'sign-in', component: AuthComponent },
  { path: 'login', redirectTo: 'sign-in', pathMatch: 'full' },
  {
    path: 'documents',
    component: AdminDashboardComponent,
    canActivate: [authGuard, adminRoleGuard],
  },
  { path: 'chat', component: ChatInterfaceComponent, canActivate: [authGuard] },
  { path: 'audit', component: AuditLogsComponent, canActivate: [authGuard, adminRoleGuard] },
  {
    path: 'chat/:id',
    component: ChatInterfaceComponent,
    canActivate: [authGuard],
  },
  {
    path: 'verification/:documentId',
    component: DocumentVerificationComponent,
    canActivate: [authGuard],
  },
  {
    path: 'graph',
    component: GraphExplorerComponent,
    canActivate: [authGuard],
  },
  {
    path: 'graph/:documentId',
    component: GraphExplorerComponent,
    canActivate: [authGuard],
  },
  { path: '**', redirectTo: 'chat' },
];
