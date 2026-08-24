import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  ScraperSyncResponse,
  ScraperStatusResponse,
} from '../models/scraper.model';

@Injectable({
  providedIn: 'root',
})
export class ScraperService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrl}/v1/scraper`;

  /**
   * Triggers an asynchronous Celery background worker to scrape circulars from the Central Bank website.
   */
  triggerSync(): Observable<ScraperSyncResponse> {
    return this.http.post<ScraperSyncResponse>(`${this.baseUrl}/sync`, {});
  }

  /**
   * Polls the status of an active or completed background scraping task.
   */
  getStatus(taskId: string): Observable<ScraperStatusResponse> {
    return this.http.get<ScraperStatusResponse>(
      `${this.baseUrl}/status/${taskId}`,
    );
  }
}
