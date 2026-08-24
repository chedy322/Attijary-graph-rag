import {
  Component,
  Input,
  Output,
  EventEmitter,
  inject,
  OnInit,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { UserRole } from '../../core/models';
import { AuthService } from '../../core/services';

interface MenuItem {
  label: string;
  route: string;
  icon: string;
  category?: string;
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.scss',
})
export class SidebarComponent implements OnInit {
  private authService = inject(AuthService);

  @Input() userRole: UserRole = 'ADMIN';
  @Input() isCollapsed = false;
  @Output() roleChange = new EventEmitter<UserRole>();
  @Output() toggleCollapse = new EventEmitter<void>();

  currentUser = {
    firstname: 'Admin',
    lastname: 'User',
    email: 'admin@centralbank.int',
    role: 'ADMIN' as UserRole,
  };

  adminMenuItems: MenuItem[] = [
    {
      label: 'Dashboard',
      route: '/dashboard',
      icon: 'grid',
      category: 'ADMINISTRATION',
    },
    { label: 'Documents', route: '/documents', icon: 'file-text' },
    { label: 'Ingestion Pipeline', route: '/dashboard', icon: 'cpu' },
    { label: 'Web Scrapers', route: '/scrapers', icon: 'globe' },
    { label: 'Graph Explorer', route: '/graph', icon: 'share-2' },
    { label: 'Users & Roles', route: '/users', icon: 'users' },
    { label: 'Audit Logs', route: '/audit', icon: 'shield' },
    { label: 'System Settings', route: '/settings', icon: 'settings' },
  ];

  userMenuItems: MenuItem[] = [
    { label: 'Chat', route: '/chat', icon: 'message-square' },
    { label: 'Documents', route: '/documents', icon: 'file-text' },
    { label: 'Regulations', route: '/regulations', icon: 'book' },
    { label: 'Graph Explorer', route: '/graph', icon: 'share-2' },
    { label: 'Analytics', route: '/analytics', icon: 'bar-chart' },
    { label: 'Bookmarks', route: '/bookmarks', icon: 'bookmark' },
    { label: 'Alerts', route: '/alerts', icon: 'bell' },
    { label: 'Settings', route: '/settings', icon: 'settings' },
  ];

  ngOnInit(): void {
    const userProfile = this.authService.currentUser();
    if (userProfile) {
      this.currentUser = {
        firstname: userProfile.firstname,
        lastname: userProfile.lastname,
        email: userProfile.email,
        role: userProfile.role,
      };
      this.userRole = userProfile.role;
    } else {
      this.currentUser.role = this.userRole;
    }
  }

  get menuItems(): MenuItem[] {
    return this.userRole === 'ADMIN' ? this.adminMenuItems : this.userMenuItems;
  }

  switchRole(role: UserRole): void {
    this.userRole = role;
    this.currentUser.role = role;
    if (role === 'USER') {
      this.currentUser.firstname = 'Michael';
      this.currentUser.lastname = 'Anderson';
      this.currentUser.email = 'michael.anderson@cbank.int';
    } else {
      this.currentUser.firstname = 'Admin';
      this.currentUser.lastname = 'User';
      this.currentUser.email = 'admin@centralbank.int';
    }
    this.roleChange.emit(role);
  }

  onToggleCollapse(): void {
    this.isCollapsed = !this.isCollapsed;
    this.toggleCollapse.emit();
  }
}
