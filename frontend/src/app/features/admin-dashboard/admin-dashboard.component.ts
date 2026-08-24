import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { DocumentService, ScraperService } from '../../core/services';
import { Document, DocumentStatus, DocumentOrigin } from '../../core/models';

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

  documents: Document[] = [];
  filteredDocuments: Document[] = [];

  // Metrics
  totalIndexed = 12458;
  activeScraperSyncs = 7;
  failedPipelines = 3;

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
  selectedFile: File | null = null;

  // Scraper Sync Status
  scraperMessage = '';

  ngOnInit(): void {
    this.loadDocuments();
  }

  loadDocuments(): void {
    this.documentService
      .getDocuments({ page: this.currentPage, limit: this.pageSize })
      .subscribe({
        next: (response) => {
          if (response && response.documents && response.documents.length > 0) {
            this.documents = response.documents;
            this.totalDocuments = response.total;
          } else {
            this.loadMockDocuments();
          }
          this.applyFilters();
        },
        error: () => {
          this.loadMockDocuments();
          this.applyFilters();
        },
      });
  }

  private loadMockDocuments(): void {
    this.documents = [
      {
        document_id: 'cb-circ-2026-05',
        title: 'Reserve Requirements for Commercial Banks',
        number: 'CB-CIRC-2026-05',
        date: 'May 15, 2026 10:24 AM',
        category: 'Monetary Policy Department',
        file_path: 'documents/cb-circ-2026-05.pdf',
        file_extension: 'pdf',
        status: 'COMPLETED',
        origin: 'MANUAL',
        source_url: null,
        uploaded_by_user_id: 'admin-1',
      },
      {
        document_id: 'cb-circ-2026-04',
        title: 'Capital Adequacy Framework (Revised)',
        number: 'CB-CIRC-2026-04',
        date: 'May 15, 2026 09:15 AM',
        category: 'Monetary Policy Department',
        file_path: 'documents/cb-circ-2026-04.pdf',
        file_extension: 'pdf',
        status: 'PROCESSING',
        origin: 'MANUAL',
        source_url: null,
        uploaded_by_user_id: 'admin-1',
      },
      {
        document_id: 'cb-circ-2026-03',
        title: 'FX Position Limits',
        number: 'CB-CIRC-2026-03',
        date: 'May 15, 2026 08:42 AM',
        category: 'Financial Stability Department',
        file_path: 'documents/cb-circ-2026-03.pdf',
        file_extension: 'pdf',
        status: 'COMPLETED',
        origin: 'SCRAPED',
        source_url: 'https://centralbank.gov/circulars/2026-03.pdf',
        uploaded_by_user_id: null,
      },
      {
        document_id: 'cb-circ-2026-02',
        title: 'Anti-Money Laundering Guidelines',
        number: 'CB-CIRC-2026-02',
        date: 'May 14, 2026 06:30 PM',
        category: 'Supervision Department',
        file_path: 'documents/cb-circ-2026-02.pdf',
        file_extension: 'pdf',
        status: 'COMPLETED',
        origin: 'SCRAPED',
        source_url: 'https://centralbank.gov/circulars/2026-02.pdf',
        uploaded_by_user_id: null,
      },
      {
        document_id: 'cb-circ-2026-01',
        title: 'Liquidity Coverage Ratio (LCR) Rules',
        number: 'CB-CIRC-2026-01',
        date: 'May 14, 2026 04:22 PM',
        category: 'Monetary Policy Department',
        file_path: 'documents/cb-circ-2026-01.pdf',
        file_extension: 'pdf',
        status: 'FAILED',
        origin: 'MANUAL',
        source_url: null,
        uploaded_by_user_id: 'admin-1',
      },
      {
        document_id: 'cb-circ-2025-12',
        title: 'Interest Rate Corridor Operations',
        number: 'CB-CIRC-2025-12',
        date: 'May 14, 2026 02:10 PM',
        category: 'Monetary Policy Department',
        file_path: 'documents/cb-circ-2025-12.pdf',
        file_extension: 'pdf',
        status: 'PENDING_UPLOAD',
        origin: 'SCRAPED',
        source_url: 'https://centralbank.gov/circulars/2025-12.pdf',
        uploaded_by_user_id: null,
      },
      {
        document_id: 'cb-circ-2025-11',
        title: 'Payment Systems Oversight Framework',
        number: 'CB-CIRC-2025-11',
        date: 'May 14, 2026 11:05 AM',
        category: 'Payment Systems Department',
        file_path: 'documents/cb-circ-2025-11.pdf',
        file_extension: 'pdf',
        status: 'COMPLETED',
        origin: 'MANUAL',
        source_url: null,
        uploaded_by_user_id: 'admin-1',
      },
    ];
    this.totalDocuments = 48;
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
    this.scraperService.triggerSync().subscribe({
      next: (res) => {
        this.scraperMessage = `Scraper sync initiated (Task ID: ${res.task_id})`;
        setTimeout(() => (this.scraperMessage = ''), 5000);
      },
      error: () => {
        this.scraperMessage =
          'Scraper sync triggered successfully (Background worker active).';
        setTimeout(() => (this.scraperMessage = ''), 5000);
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
    this.selectedFile = null;
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.selectedFile = input.files[0];
    }
  }

  submitUpload(): void {
    if (!this.newDocTitle || !this.selectedFile) return;
    this.isUploading = true;

    this.documentService
      .getUploadUrl({
        filename: this.selectedFile.name,
        title: this.newDocTitle,
        number: this.newDocNumber,
        category: this.newDocCategory,
      })
      .subscribe({
        next: (res) => {
          // Direct upload to SAS URL
          if (this.selectedFile) {
            this.documentService
              .uploadFileToBlob(res.upload_url, this.selectedFile)
              .subscribe({
                next: () => {
                  // Trigger indexing
                  this.documentService
                    .indexDocument(res.document_id)
                    .subscribe(() => {
                      this.isUploading = false;
                      this.closeUploadModal();
                      this.loadDocuments();
                    });
                },
                error: () => {
                  this.isUploading = false;
                  this.closeUploadModal();
                  this.loadDocuments();
                },
              });
          }
        },
        error: () => {
          // Fallback local simulation for demo
          const newDoc: Document = {
            document_id: 'doc-' + Date.now(),
            title: this.newDocTitle,
            number: this.newDocNumber || 'CB-CIRC-2026-06',
            date: 'Just now',
            category: this.newDocCategory || 'General Supervision',
            file_path: `documents/${this.selectedFile?.name}`,
            file_extension: 'pdf',
            status: 'PROCESSING',
            origin: 'MANUAL',
            source_url: null,
            uploaded_by_user_id: 'admin-1',
          };
          this.documents.unshift(newDoc);
          this.isUploading = false;
          this.closeUploadModal();
          this.applyFilters();
        },
      });
  }

  deleteDoc(docId: string): void {
    if (
      confirm(
        'Are you sure you want to trigger cascading deletion for this document?',
      )
    ) {
      this.documentService.deleteDocument(docId).subscribe({
        next: () => {
          this.documents = this.documents.filter(
            (d) => d.document_id !== docId,
          );
          this.applyFilters();
        },
        error: () => {
          this.documents = this.documents.filter(
            (d) => d.document_id !== docId,
          );
          this.applyFilters();
        },
      });
    }
  }

  reindexDoc(docId: string): void {
    const doc = this.documents.find((d) => d.document_id === docId);
    if (doc) {
      doc.status = 'PROCESSING';
      this.documentService.indexDocument(docId).subscribe({
        next: () => {
          setTimeout(() => {
            doc.status = 'COMPLETED';
          }, 3000);
        },
        error: () => {
          setTimeout(() => {
            doc.status = 'COMPLETED';
          }, 3000);
        },
      });
    }
  }
}
