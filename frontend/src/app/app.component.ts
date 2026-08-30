import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, Router } from '@angular/router';
import { SidebarComponent } from './layout/sidebar/sidebar.component';
import { ApiErrorService, AuthService } from './core/services';
import { UserRole } from './core/models';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, SidebarComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent {
  title = 'GraphRAG Regulatory Intelligence Platform';
  authService = inject(AuthService);
  apiErrorService = inject(ApiErrorService);
  router = inject(Router);

  isSidebarCollapsed = false;

  get isAuthPage(): boolean {
    return this.router.url.includes('/auth') || this.router.url.includes('/sign-in');
  }

  get currentUserRole(): UserRole | null {
    return this.authService.currentUser()?.role || null;
  }

  onToggleSidebar(): void {
    this.isSidebarCollapsed = !this.isSidebarCollapsed;
  }
}
