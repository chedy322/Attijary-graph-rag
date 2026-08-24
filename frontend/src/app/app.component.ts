import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, Router } from '@angular/router';
import { SidebarComponent } from './layout/sidebar/sidebar.component';
import { AuthService } from './core/services';
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
  router = inject(Router);

  isSidebarCollapsed = false;

  get isAuthPage(): boolean {
    return this.router.url.includes('/auth');
  }

  get currentUserRole(): UserRole {
    return this.authService.currentUser()?.role || 'ADMIN';
  }

  onRoleChanged(role: UserRole): void {
    const curr = this.authService.currentUser();
    if (curr) {
      this.authService.currentUser.set({ ...curr, role });
    }
  }

  onToggleSidebar(): void {
    this.isSidebarCollapsed = !this.isSidebarCollapsed;
  }
}
