export type DocumentStatus =
  | 'PENDING_UPLOAD'
  | 'PROCESSING'
  | 'COMPLETED'
  | 'FAILED'
  | 'PENDING_DELETE';

export type DocumentOrigin = 'SCRAPED' | 'MANUAL';

export interface Document {
  document_id: string;
  title: string;
  number: string | null;
  date: string;
  category: string | null;
  file_path: string;
  file_extension: string | null;
  status: DocumentStatus;
  origin: DocumentOrigin;
  source_url: string | null;
  uploaded_by_user_id: string | null;
}

export interface DocumentFilterParams {
  page?: number;
  limit?: number;
  status?: DocumentStatus;
}

export interface DocumentListResponse {
  total: number;
  page: number;
  limit: number;
  documents: Document[];
}

export interface UploadUrlRequest {
  filename: string;
  title: string;
  number: string;
  category: string;
  date: string;
}

export interface UploadUrlResponse {
  document_id: string;
  status: DocumentStatus;
  upload_url: string;
  file_path: string;
}

export interface IndexDocumentResponse {
  message: string;
  document_id: string;
  status: DocumentStatus;
  task_id: string;
}

export interface DeleteDocumentResponse {
  message: string;
  document_id: string;
  status: DocumentStatus;
  task_id: string;
}
