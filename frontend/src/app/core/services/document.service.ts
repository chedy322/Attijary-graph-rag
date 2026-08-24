import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  Document,
  DocumentFilterParams,
  DocumentListResponse,
  UploadUrlRequest,
  UploadUrlResponse,
  IndexDocumentResponse,
  DeleteDocumentResponse,
} from '../models/document.model';

@Injectable({
  providedIn: 'root',
})
export class DocumentService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrl}/v1/documents`;

  /**
   * Retrieves a paginated list of all ingested and scraped regulatory documents.
   */
  getDocuments(
    params?: DocumentFilterParams,
  ): Observable<DocumentListResponse> {
    let httpParams = new HttpParams();
    if (params?.page !== undefined) {
      httpParams = httpParams.set('page', params.page.toString());
    }
    if (params?.limit !== undefined) {
      httpParams = httpParams.set('limit', params.limit.toString());
    }
    if (params?.status) {
      httpParams = httpParams.set('status', params.status);
    }
    return this.http.get<DocumentListResponse>(this.baseUrl, {
      params: httpParams,
    });
  }

  /**
   * Retrieves detailed metadata, origin details, and current ETL state for a specific document.
   */
  getDocumentById(documentId: string): Observable<Document> {
    return this.http.get<Document>(`${this.baseUrl}/${documentId}`);
  }

  /**
   * Prepares the database record (PENDING_UPLOAD) and returns a pre-signed SAS upload URL.
   */
  getUploadUrl(request: UploadUrlRequest): Observable<UploadUrlResponse> {
    return this.http.post<UploadUrlResponse>(
      `${this.baseUrl}/upload-url`,
      request,
    );
  }

  /**
   * Uploads the file binary directly to blob storage using the pre-signed SAS upload URL.
   */
  uploadFileToBlob(uploadUrl: string, file: File): Observable<void> {
    return this.http.put<void>(uploadUrl, file, {
      headers: {
        'Content-Type': file.type || 'application/octet-stream',
      },
    });
  }

  /**
   * Triggers the background AI indexing pipeline after file upload to storage succeeds.
   */
  indexDocument(documentId: string): Observable<IndexDocumentResponse> {
    return this.http.post<IndexDocumentResponse>(
      `${this.baseUrl}/${documentId}/index`,
      {},
    );
  }

  /**
   * Initiates an asynchronous cascading deletion of the document across DB, Vector DB, and Neo4j.
   */
  deleteDocument(documentId: string): Observable<DeleteDocumentResponse> {
    return this.http.delete<DeleteDocumentResponse>(
      `${this.baseUrl}/${documentId}`,
    );
  }
}
