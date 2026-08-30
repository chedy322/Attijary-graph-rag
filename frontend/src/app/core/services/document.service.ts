import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
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
    return this.http.get<{
      status: string;
      data: Document[];
      meta: { total: number; page: number; limit: number };
    }>(this.baseUrl, { params: httpParams }).pipe(
      map((res) => ({
        documents: res.data,
        total: res.meta.total,
        page: res.meta.page,
        limit: res.meta.limit,
      })),
    );
  }

  /**
   * Retrieves detailed metadata, origin details, and current ETL state for a specific document.
   */
  getDocumentById(documentId: string): Observable<Document> {
    return this.http.get<{ data: Document }>(`${this.baseUrl}/${documentId}`).pipe(
      map((res) => res.data)
    );
  }

  /**
   * Prepares the database record (PENDING_UPLOAD) and returns a pre-signed SAS upload URL.
   */
  getUploadUrl(request: UploadUrlRequest): Observable<UploadUrlResponse> {
    return this.http.post<{
      data: { document: Document; upload_url: string };
    }>(`${this.baseUrl}/upload-url`, request).pipe(
      map((res) => {
        const document = res.data.document;
        return {
          document_id: document.document_id,
          status: document.status,
          upload_url: res.data.upload_url,
          file_path: document.file_path,
        };
      })
    );
  }

  /**
   * Uploads the file binary directly to blob storage using the pre-signed SAS upload URL.
   */
  uploadFileToBlob(uploadUrl: string, file: File): Observable<void> {
    return this.http.put<void>(uploadUrl, file, {
      headers: {
        'Content-Type': file.type || 'application/octet-stream',
        'x-ms-blob-type': 'BlockBlob',
      },
    });
  }

  /**
   * Triggers the background AI indexing pipeline after file upload to storage succeeds.
   */
  indexDocument(documentId: string): Observable<IndexDocumentResponse> {
    return this.http.post<{ data: IndexDocumentResponse }>(`${this.baseUrl}/${documentId}/index`, {}).pipe(
      map((res) => res.data)
    );
  }

  /**
   * Initiates an asynchronous cascading deletion of the document across DB, Vector DB, and Neo4j.
   */
  deleteDocument(documentId: string): Observable<DeleteDocumentResponse> {
    return this.http.delete<{ data: DeleteDocumentResponse }>(`${this.baseUrl}/${documentId}`).pipe(
      map((res) => res.data)
    );
  }
}
