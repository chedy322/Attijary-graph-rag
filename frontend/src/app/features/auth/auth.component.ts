import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../core/services';
import { UserRole } from '../../core/models';

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

  // Form Fields
  email = 'you@centralbank.int';
  password = '';
  firstname = '';
  lastname = '';
  rolePreference: UserRole = 'ADMIN';

  returnUrl = '/dashboard';

  ngOnInit(): void {
    const returnUrlParam = this.route.snapshot.queryParams['returnUrl'];
    if (returnUrlParam) {
      this.returnUrl = returnUrlParam;
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

    // Trigger Clerk sync flow
    this.authService.login(this.email, this.rolePreference).subscribe({
      next: (profile) => {
        this.isLoading = false;
        // Redirect based on role
        if (profile.role === 'ADMIN') {
          this.router.navigate(['/dashboard']);
        } else {
          this.router.navigate(['/chat']);
        }
      },
      error: () => {
        this.isLoading = false;
        // Fallback navigation
        if (this.rolePreference === 'ADMIN') {
          this.router.navigate(['/dashboard']);
        } else {
          this.router.navigate(['/chat']);
        }
      },
    });
  }

  signInWithSSO(): void {
    this.onSubmit();
  }
}
