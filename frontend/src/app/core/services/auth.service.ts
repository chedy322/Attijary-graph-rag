import { Injectable, signal, computed, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import {
  Observable,
  tap,
  catchError,
  throwError,
  from,
  switchMap,
  firstValueFrom,
  BehaviorSubject,
  map,
} from 'rxjs';
import { environment } from '../../../environments/environment';
import { UserProfile, UserSyncRequest } from '../models/user.model';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private http = inject(HttpClient);

  currentUser = signal<UserProfile | null>(null);
  readonly currentUser$ = new BehaviorSubject<UserProfile | null>(null);
  isLoaded = signal<boolean>(false);
  isBackendSynced = signal<boolean>(false);
  sessionToken = signal<string | null>(null);

  isLoggedIn = computed(() => !!this.sessionToken());
  isAuthenticated = computed(
    () => this.isLoaded() && this.isLoggedIn() && this.isBackendSynced(),
  );
  isAdmin = computed(() => this.currentUser()?.role === 'ADMIN');
  isAdmin$ = this.currentUser$.pipe(map((user) => user?.role === 'ADMIN'));
  isUser$ = this.currentUser$.pipe(
    map((user) => user?.role === 'USER' || user?.role === 'ADMIN'),
  );
  private initialization?: Promise<void>;

  private async waitForClerk(maxRetries = 100, delayMs = 100): Promise<any> {
    if (typeof window === 'undefined') return null;

    for (let i = 0; i < maxRetries; i++) {
      const clerk = (window as any).Clerk;
      if (clerk) {
        if (!clerk.loaded && typeof clerk.load === 'function') {
          await clerk.load();
        }
        if (clerk.loaded || clerk.isReady) {
          return clerk;
        }
      }
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
    return null;
  }

  initialize(): Promise<void> {
    if (!this.initialization) {
      this.initialization = this.initializeClerkSession();
    }
    return this.initialization;
  }

  private async initializeClerkSession(): Promise<void> {
    const clerk = await this.waitForClerk();
    if (!clerk) {
      this.clearSession();
      this.isLoaded.set(true);
      return;
    }

    await this.applyClerkState(clerk);
    if (typeof clerk.addListener === 'function') {
      clerk.addListener((state: unknown) => {
        void this.applyClerkState(state);
      });
    }
  }

  private async applyClerkState(stateOrClerk: any): Promise<void> {
    const user = stateOrClerk?.user;
    const session = stateOrClerk?.session;

    if (!user || !session) {
      this.clearSession();
      this.isLoaded.set(true);
      return;
    }

    try {
      const token = await session.getToken({
        template: 'graph-rag-jwt', 
      });
      if (!token) {
        throw new Error('Clerk session did not provide a token.');
      }
      this.sessionToken.set(token);
      await firstValueFrom(this.syncUserWithBackend(this.toSyncRequest(user)));
    } catch (error) {
      console.error('Clerk session synchronization failed:', error);
      this.clearSession();
    } finally {
      this.isLoaded.set(true);
    }
  }

  private toSyncRequest(user: any): UserSyncRequest {
    return {
      firstname: user.firstName || '',
      lastname: user.lastName || '',
      email: user.primaryEmailAddress?.emailAddress || user.emailAddresses?.[0]?.emailAddress || '',
      clerk_id: user.id,
    };
  }

  private clearSession(): void {
    this.currentUser.set(null);
    this.currentUser$.next(null);
    this.sessionToken.set(null);
    this.isBackendSynced.set(false);
  }

  async getClerkToken(): Promise<string | null> {
    // return this.sessionToken();
    const clerk = (window as any).Clerk;
  if (!clerk?.session) return null;
  
  // Fetch fresh JWT dynamically using your template name
  return await clerk.session.getToken({ template: 'graph-rag-jwt' });
  }

  syncUserWithBackend(userData?: UserSyncRequest): Observable<UserProfile> {
    const syncUrl = `${environment.apiUrl}/v1/sync`;

    return this.http.post<UserProfile>(syncUrl, userData || {}).pipe(
      tap((profile) => {
        this.currentUser.set(profile);
        this.currentUser$.next(profile);
        this.isBackendSynced.set(true);
      }),
      catchError((err) => {
        this.currentUser.set(null);
        this.isBackendSynced.set(false);
        return throwError(() => err);
      }),
    );
  }

  login(email: string, password: string): Observable<UserProfile> {
    return from(this.ensureClerkSession(email, password)).pipe(
      switchMap(({ user }) => this.syncUserWithBackend(this.toSyncRequest(user))),
    );
  }

  private async ensureClerkSession(email: string, password: string): Promise<{ user: any }> {
    const clerk = await this.waitForClerk();
    if (!clerk) {
      throw new Error('Clerk is not ready. Please try again.');
    }

    if (clerk.session && clerk.user) {
      throw new Error('A Clerk session is already active.');
    }

    if (!clerk.client?.signIn) {
      throw new Error('Clerk sign-in is unavailable.');
    }

    try {
      const signInAttempt = await clerk.client.signIn.create({
        identifier: email,
        password,
      });

      if (signInAttempt.status !== 'complete' || !signInAttempt.createdSessionId) {
        throw new Error('Authentication was not completed by Clerk.');
      }

      await clerk.setActive({ session: signInAttempt.createdSessionId });
      const token = await clerk.session?.getToken({
        template: 'graph-rag-jwt',
      });
      if (!clerk.user || !token) {
        throw new Error('Clerk did not establish an active session.');
      }
      this.sessionToken.set(token);
      return { user: clerk.user };
    } catch (error: any) {
      const clerkError = error?.errors?.[0]?.longMessage || error?.errors?.[0]?.message;
      throw new Error(clerkError || error?.message || 'Invalid credentials.');
    }
  }

  logout(): void {
    if (typeof window !== 'undefined' && (window as any).Clerk?.signOut) {
      void (window as any).Clerk.signOut();
    }
    this.clearSession();
    this.isLoaded.set(true);
  }
}