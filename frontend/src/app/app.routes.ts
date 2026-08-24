import { Routes } from '@angular/router';
import { AuthComponent } from './features/auth/auth.component';
import { AdminDashboardComponent } from './features/admin-dashboard/admin-dashboard.component';
import { ChatInterfaceComponent } from './features/chat-interface/chat-interface.component';
import { DocumentVerificationComponent } from './features/document-verification/document-verification.component';
import { GraphExplorerComponent } from './features/graph-explorer/graph-explorer.component';
import { authGuard } from './core/guards/auth.guard';
import { roleGuard } from './core/guards/role.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  { path: 'auth', component: AuthComponent },
  {
    path: 'dashboard',
    component: AdminDashboardComponent,
    canActivate: [authGuard, roleGuard],
  },
  {
    path: 'documents',
    component: AdminDashboardComponent,
    canActivate: [authGuard, roleGuard],
  },
  { path: 'chat', component: ChatInterfaceComponent, canActivate: [authGuard] },
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
  { path: '**', redirectTo: 'dashboard' },
];
