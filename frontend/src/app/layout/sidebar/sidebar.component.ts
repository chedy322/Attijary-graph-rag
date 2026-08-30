import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { UserRole } from '../../core/models';
import { AuthService } from '../../core/services';

interface MenuItem {
  label: string;
  route: string;
  icon: string;
  category?: string;
  adminOnly?: boolean;
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.scss',
})
export class SidebarComponent {
  protected authService = inject(AuthService);

  @Input() userRole: UserRole | null = null;
  @Input() isCollapsed = false;
  @Output() toggleCollapse = new EventEmitter<void>();

  adminMenuItems: MenuItem[] = [
    { label: 'Chat', route: '/chat', icon: 'message-square' },
    { label: 'Documents', route: '/documents', icon: 'file-text', adminOnly: true },
    { label: 'Web Scrapers', route: '/scrapers', icon: 'globe', adminOnly: true },
    { label: 'Graph Explorer', route: '/graph', icon: 'share-2', adminOnly: true },
    { label: 'Users & Roles', route: '/users', icon: 'users', adminOnly: true },
    { label: 'Audit Logs', route: '/audit', icon: 'shield', adminOnly: true },
    { label: 'System Settings', route: '/settings', icon: 'settings', adminOnly: true },
  ];

  userMenuItems: MenuItem[] = [
    { label: 'Chat', route: '/chat', icon: 'message-square' },
  ];

  get currentUser() {
    return this.authService.currentUser();
  }

  get menuItems(): MenuItem[] {
    return this.authService.isAdmin() ? this.adminMenuItems : this.userMenuItems;
  }

  get isAdmin(): boolean {
    return this.authService.isAdmin();
  }

  get userInitials(): string {
    const firstname = this.currentUser?.firstname?.trim() || '';
    const lastname = this.currentUser?.lastname?.trim() || '';
    return `${firstname.charAt(0)}${lastname.charAt(0)}`.toUpperCase();
  }

  onToggleCollapse(): void {
    this.isCollapsed = !this.isCollapsed;
    this.toggleCollapse.emit();
  }
}
