import { Injectable, signal, computed, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap, catchError, of } from 'rxjs';
import { environment } from '../../../environments/environment';
import { UserProfile, UserSyncRequest } from '../models/user.model';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private http = inject(HttpClient);

  // Reactive state using Angular Signals
  currentUser = signal<UserProfile | null>(null);
  isLoaded = signal<boolean>(false);
  sessionToken = signal<string | null>(null);

  // Computed signals
  isLoggedIn = computed(() => !!this.currentUser());
  isAdmin = computed(() => this.currentUser()?.role === 'ADMIN');

  constructor() {
    this.initClerkListener();
  }

  /**
   * Listens to Clerk authentication state changes if Clerk JS SDK is available in window.
   */
  private initClerkListener(): void {
    if (typeof window !== 'undefined' && (window as any).Clerk) {
      const clerk = (window as any).Clerk;
      clerk.addListener((state: any) => {
        if (state.user) {
          const clerkUser = state.user;
          const token = state.session
            ? state.session.lastActiveToken?.jwt
            : null;
          this.sessionToken.set(token);
          this.syncUserWithBackend({
            firstname: clerkUser.firstName || 'User',
            lastname: clerkUser.lastName || '',
            email: clerkUser.primaryEmailAddress?.emailAddress || '',
            clerk_id: clerkUser.id,
          }).subscribe();
        } else {
          this.currentUser.set(null);
          this.sessionToken.set(null);
          this.isLoaded.set(true);
        }
      });
    } else {
      this.isLoaded.set(true);
    }
  }

  /**
   * Synchronizes user metadata with backend database (POST /api/v1/sync).
   */
  syncUserWithBackend(userData?: UserSyncRequest): Observable<UserProfile> {
    const payload: UserSyncRequest = userData || {
      firstname: this.currentUser()?.firstname || 'Michael',
      lastname: this.currentUser()?.lastname || 'Anderson',
      email: this.currentUser()?.email || 'michael.anderson@cbank.int',
    };

    const syncUrl = `${environment.apiUrl}/v1/sync`;

    return this.http.post<UserProfile>(syncUrl, payload).pipe(
      tap((profile) => {
        this.currentUser.set(profile);
        this.isLoaded.set(true);
      }),
      catchError(() => {
        // Fallback for dev / offline demo sync
        const fallbackRole: 'ADMIN' | 'USER' = payload.email.includes('admin')
          ? 'ADMIN'
          : 'USER';
        const profile: UserProfile = {
          user_id: payload.clerk_id || 'usr_' + Date.now(),
          firstname: payload.firstname,
          lastname: payload.lastname,
          email: payload.email,
          role: fallbackRole,
        };
        this.currentUser.set(profile);
        this.isLoaded.set(true);
        return of(profile);
      }),
    );
  }

  /**
   * Returns current JWT session token for HTTP interceptor.
   */
  async getClerkToken(): Promise<string | null> {
    if (typeof window !== 'undefined' && (window as any).Clerk?.session) {
      try {
        const token = await (window as any).Clerk.session.getToken();
        this.sessionToken.set(token);
        return token;
      } catch {
        return this.sessionToken();
      }
    }
    return this.sessionToken();
  }

  /**
   * Performs login & sync.
   */
  login(
    email: string,
    rolePreference: 'ADMIN' | 'USER' = 'USER',
  ): Observable<UserProfile> {
    const names = email.split('@')[0].split('.');
    const firstname = names[0]
      ? names[0].charAt(0).toUpperCase() + names[0].slice(1)
      : 'User';
    const lastname = names[1]
      ? names[1].charAt(0).toUpperCase() + names[1].slice(1)
      : 'Compliance';

    const req: UserSyncRequest = {
      firstname,
      lastname,
      email,
    };

    return this.syncUserWithBackend(req).pipe(
      tap((profile) => {
        if (profile) {
          profile.role = rolePreference;
          this.currentUser.set({ ...profile });
        }
      }),
    );
  }

  logout(): void {
    if (typeof window !== 'undefined' && (window as any).Clerk) {
      (window as any).Clerk.signOut();
    }
    this.currentUser.set(null);
    this.sessionToken.set(null);
  }
}
