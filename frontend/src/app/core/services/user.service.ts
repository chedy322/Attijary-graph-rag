import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { UserSyncRequest, UserSyncResponse } from '../models/user.model';

@Injectable({
  providedIn: 'root',
})
export class UserService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrl}/v1`;

  /**
   * Synchronizes user metadata with PostgreSQL after Clerk authentication.
   */
  syncUser(user: UserSyncRequest): Observable<UserSyncResponse> {
    return this.http.post<UserSyncResponse>(`${this.baseUrl}/sync`, user);
  }
}
