import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { AuthService, DocumentService, ScraperService } from '../../core/services';
import { Document } from '../../core/models';

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './admin-dashboard.component.html',
  styleUrl: './admin-dashboard.component.scss',
})
export class AdminDashboardComponent implements OnInit {
  private documentService = inject(DocumentService);
  private scraperService = inject(ScraperService);
  protected authService = inject(AuthService);

  documents: Document[] = [];
  filteredDocuments: Document[] = [];

  // State Management
  isLoading = false;
  errorMessage: string | null = null;
  scraperMessage: string | null = null;

  // Search & Filters
  searchTerm = '';
  selectedOrigin: string = 'ALL';
  selectedStatus: string = 'ALL';

  // Pagination
  currentPage = 1;
  pageSize = 10;
  totalDocuments = 0;

  // Upload Modal State
  showUploadModal = false;
  isUploading = false;
  newDocTitle = '';
  newDocNumber = '';
  newDocCategory = '';
  newDocDate = '';
  selectedFile: File | null = null;

  ngOnInit(): void {
    this.loadDocuments();
  }

  get totalIndexed(): number {
    return this.totalDocuments || this.documents.length;
  }

  get activeScraperSyncs(): number {
    return this.documents.filter((d) => d.status === 'PROCESSING').length;
  }

  get failedPipelines(): number {
    return this.documents.filter((d) => d.status === 'FAILED').length;
  }

  clearError(): void {
    this.errorMessage = null;
  }

  loadDocuments(): void {
    this.isLoading = true;
    this.errorMessage = null;

    this.documentService
      .getDocuments({ page: this.currentPage, limit: this.pageSize })
      .subscribe({
        next: (response) => {
          this.isLoading = false;
          this.documents = response.documents || [];
          this.totalDocuments = response.total || this.documents.length;
          this.applyFilters();
        },
        error: (err) => {
          this.isLoading = false;
          this.errorMessage =
            err?.error?.message ||
            err?.message ||
            'Failed to load documents from backend service.';
          this.documents = [];
          this.filteredDocuments = [];
        },
      });
  }

  applyFilters(): void {
    this.filteredDocuments = this.documents.filter((doc) => {
      const matchesSearch =
        !this.searchTerm ||
        doc.title.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
        (doc.number &&
          doc.number.toLowerCase().includes(this.searchTerm.toLowerCase())) ||
        (doc.category &&
          doc.category.toLowerCase().includes(this.searchTerm.toLowerCase()));

      const matchesOrigin =
        this.selectedOrigin === 'ALL' || doc.origin === this.selectedOrigin;
      const matchesStatus =
        this.selectedStatus === 'ALL' || doc.status === this.selectedStatus;

      return matchesSearch && matchesOrigin && matchesStatus;
    });
  }

  triggerSyncScraper(): void {
    this.scraperMessage = 'Triggering web scraper sync...';
    this.errorMessage = null;

    this.scraperService.triggerSync().subscribe({
      next: (res) => {
        this.scraperMessage = `Scraper sync initiated (Task ID: ${res.task_id})`;
        setTimeout(() => (this.scraperMessage = null), 5000);
      },
      error: (err) => {
        this.scraperMessage = null;
        this.errorMessage =
          err?.error?.message ||
          err?.message ||
          'Failed to trigger web scraper sync on backend.';
      },
    });
  }

  openUploadModal(): void {
    this.showUploadModal = true;
  }

  closeUploadModal(): void {
    this.showUploadModal = false;
    this.newDocTitle = '';
    this.newDocNumber = '';
    this.newDocCategory = '';
    this.newDocDate = '';
    this.selectedFile = null;
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.selectedFile = input.files[0];
    }
  }

  submitUpload(): void {
    if (!this.newDocTitle || !this.newDocDate || !this.selectedFile) {
      this.errorMessage = 'Title, document date, and file are required.';
      return;
    }
    this.isUploading = true;
    this.errorMessage = null;

    this.documentService
      .getUploadUrl({
        filename: this.selectedFile.name,
        title: this.newDocTitle,
        number: this.newDocNumber,
        category: this.newDocCategory,
        date: this.newDocDate,
      })
      .subscribe({
        next: (res) => {
          if (this.selectedFile) {
            this.documentService
              .uploadFileToBlob(res.upload_url, this.selectedFile)
              .subscribe({
                next: () => {
                  this.documentService
                    .indexDocument(res.document_id)
                    .subscribe({
                      next: () => {
                        this.isUploading = false;
                        this.closeUploadModal();
                        this.loadDocuments();
                      },
                      error: (err) => {
                        this.isUploading = false;
                        this.errorMessage =
                          err?.error?.message ||
                          'Failed to index document after upload.';
                      },
                    });
                },
                error: (err) => {
                  this.isUploading = false;
                  this.errorMessage =
                    err?.error?.message ||
                    'Failed to push file binary to storage.';
                },
              });
          }
        },
        error: (err) => {
          this.isUploading = false;
          this.errorMessage =
            err?.error?.message ||
            err?.message ||
            'Failed to obtain pre-signed upload SAS token.';
        },
      });
  }

  deleteDoc(docId: string): void {
    if (
      !confirm(
        'Are you sure you want to trigger cascading deletion for this document?',
      )
    ) {
      return;
    }

    this.errorMessage = null;
    this.documentService.deleteDocument(docId).subscribe({
      next: () => {
        // Strict Lifecycle Update only on HTTP 200/204 success
        this.documents = this.documents.filter((d) => d.document_id !== docId);
        this.applyFilters();
      },
      error: (err) => {
        this.errorMessage =
          err?.error?.message ||
          err?.message ||
          `Failed to delete document ${docId} on backend.`;
      },
    });
  }

  reindexDoc(docId: string): void {
    this.errorMessage = null;
    this.documentService.indexDocument(docId).subscribe({
      next: (res) => {
        const doc = this.documents.find((d) => d.document_id === docId);
        if (doc) {
          doc.status = res.status || 'PROCESSING';
        }
        this.applyFilters();
      },
      error: (err) => {
        this.errorMessage =
          err?.error?.message ||
          err?.message ||
          `Failed to trigger re-indexing for document ${docId}.`;
      },
    });
  }

  canTriggerIndex(status: Document['status']): boolean {
    return status !== 'PROCESSING' && status !== 'COMPLETED';
  }
}
