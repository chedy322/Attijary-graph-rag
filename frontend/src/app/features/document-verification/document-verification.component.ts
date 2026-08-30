import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, ActivatedRoute } from '@angular/router';
import { DocumentService } from '../../core/services';
import { Document } from '../../core/models';

@Component({
  selector: 'app-document-verification',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './document-verification.component.html',
  styleUrl: './document-verification.component.scss',
})
export class DocumentVerificationComponent implements OnInit {
  private documentService = inject(DocumentService);
  private route = inject(ActivatedRoute);

  documentId = '';
  document: Document | null = null;

  // Viewer State
  currentPage = 1;
  totalPages = 1;
  zoomLevel = 100;
  showThumbnails = true;

  // AI Verification State
  userQuestion = '';
  aiAnswer = '';
  highlightedText = '';
  confidenceScore: number | null = null;
  sourceCitation = '';

  ngOnInit(): void {
    this.route.params.subscribe((params) => {
      if (params['documentId']) {
        this.documentId = params['documentId'];
      }
      if (this.documentId) {
        this.loadDocumentDetails();
      } else {
        this.errorMessage = 'A document ID is required to view verification details.';
      }
    });
  }

  errorMessage: string | null = null;

  loadDocumentDetails(): void {
    this.errorMessage = null;
    this.documentService.getDocumentById(this.documentId).subscribe({
      next: (doc) => {
        this.document = doc;
      },
      error: (err) => {
        this.errorMessage = err?.error?.message || err?.message || 'Failed to load document verification details.';
        this.document = null;
      },
    });
  }

  changePage(newPage: number): void {
    if (newPage >= 1 && newPage <= this.totalPages) {
      this.currentPage = newPage;
    }
  }

  zoomIn(): void {
    if (this.zoomLevel < 200) this.zoomLevel += 10;
  }

  zoomOut(): void {
    if (this.zoomLevel > 50) this.zoomLevel -= 10;
  }

  toggleThumbnails(): void {
    this.showThumbnails = !this.showThumbnails;
  }
}
