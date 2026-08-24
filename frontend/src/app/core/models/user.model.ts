export type UserRole = 'ADMIN' | 'USER';

export interface User {
  user_id: string;
  firstname: string;
  lastname: string;
  email: string;
  role: UserRole;
  created_at: string;
  updated_at: string;
  clerk_id?: string | null;
}

export interface UserSyncRequest {
  firstname: string;
  lastname: string;
  email: string;
  clerk_id?: string;
}

export interface UserSyncResponse {
  user_id: string;
  firstname: string;
  lastname: string;
  email: string;
  role: UserRole;
}

export interface UserProfile {
  user_id: string;
  firstname: string;
  lastname: string;
  email: string;
  role: 'ADMIN' | 'USER';
}
