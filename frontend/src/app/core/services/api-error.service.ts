import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ApiErrorService {
  readonly message = signal<string | null>(null);

  show(error: unknown): void {
    const response = error as { error?: { message?: string }; message?: string };
    this.message.set(
      response.error?.message || response.message || 'The request could not be completed.',
    );
  }

  clear(): void {
    this.message.set(null);
  }
}
