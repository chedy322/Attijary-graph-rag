export interface ScraperSyncResponse {
  message: string;
  task_id: string;
}

export interface ScraperTaskResult {
  scraped_pages: number;
  new_documents_found: number;
  indexed_document_ids: string[];
}

export interface ScraperStatusResponse {
  task_id: string;
  status: 'PENDING' | 'STARTED' | 'SUCCESS' | 'FAILURE' | 'RETRY' | string;
  result?: ScraperTaskResult;
}
