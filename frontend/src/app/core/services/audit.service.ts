import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AuditLog } from '../models/audit-log.model';

export interface AuditLogsResponse {
  status: string;
  data: AuditLog[];
  meta: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
}

@Injectable({ providedIn: 'root' })
export class AuditService {
  private http = inject(HttpClient);
  private readonly endpoint = `${environment.apiUrl}/v1/audits/logs`;

  getLogs(page = 1, limit = 10): Observable<AuditLogsResponse> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('limit', limit.toString());
    return this.http.get<AuditLogsResponse>(this.endpoint, { params });
  }
}
