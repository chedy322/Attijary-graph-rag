import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../core/services';

@Component({
  selector: 'app-auth',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './auth.component.html',
  styleUrl: './auth.component.scss',
})
export class AuthComponent implements OnInit {
  private authService = inject(AuthService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  activeTab: 'signin' | 'signup' = 'signin';
  showPassword = false;
  isLoading = false;
  errorMessage: string | null = null;

  // Form Fields - Ensure all properties used in template exist here
  email = '';
  password = '';
  firstname = ''; // Added to match [(ngModel)]="firstname"
  lastname = '';  // Added to fix the NG9 error

  returnUrl = '/chat';

  ngOnInit(): void {
    const returnUrlParam = this.route.snapshot.queryParams['returnUrl'];
    if (returnUrlParam) {
      this.returnUrl = returnUrlParam;
    }
    if (this.authService.isAuthenticated()) {
      void this.router.navigateByUrl(this.returnUrl);
    }
  }

  setTab(tab: 'signin' | 'signup'): void {
    this.activeTab = tab;
  }

  toggleShowPassword(): void {
    this.showPassword = !this.showPassword;
  }

  onSubmit(): void {
    if (!this.email || this.isLoading) return;

    this.isLoading = true;
    this.errorMessage = null;

    this.authService.login(this.email, this.password).subscribe({
      next: (profile) => {
        this.isLoading = false;
        this.router.navigate([
          profile?.role === 'ADMIN' ? '/documents' : '/chat',
        ]);
      },
      error: (err) => {
        this.isLoading = false;
        console.error('Login/Sync failed:', err);
        this.errorMessage =
          err?.error?.message ||
          err?.message ||
          'Failed to sync user with backend server.';
      },
    });
  }

  signInWithSSO(): void {
    this.onSubmit();
  }
}