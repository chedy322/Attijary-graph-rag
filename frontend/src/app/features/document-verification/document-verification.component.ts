import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, ActivatedRoute } from '@angular/router';
import { DocumentService, AgentService } from '../../core/services';
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
  private agentService = inject(AgentService);
  private route = inject(ActivatedRoute);

  documentId = 'cb-circ-2026-05';
  document: Document | null = null;

  // Viewer State
  currentPage = 4;
  totalPages = 24;
  zoomLevel = 100;
  showThumbnails = true;

  // AI Verification State
  userQuestion =
    'What are the current reserve requirements for commercial banks in local currency?';
  aiAnswer =
    'According to Circular N° 2026-05 - Reserve Requirements for Commercial Banks, the reserve requirements for commercial banks in local currency are as follows:';
  highlightedText =
    'Banks must maintain reserve balances in eligible accounts with the Central Bank as follows: (a) Demand deposits: 10% of the total amount; (b) Time and savings deposits: 5% of the total amount. These requirements are applicable to all banks licensed by the Central Bank.';
  confidenceScore = 88.5;
  sourceCitation = 'Source: Circular N° 2026-05, Section 3.1, Page 4';

  ngOnInit(): void {
    this.route.params.subscribe((params) => {
      if (params['documentId']) {
        this.documentId = params['documentId'];
      }
      this.loadDocumentDetails();
    });
  }

  loadDocumentDetails(): void {
    this.documentService.getDocumentById(this.documentId).subscribe({
      next: (doc) => {
        this.document = doc;
      },
      error: () => {
        this.document = {
          document_id: this.documentId,
          title:
            'Circular N° 2026-05 - Reserve Requirements for Commercial Banks',
          number: 'CB-CIRC-2026-05',
          date: 'May 10, 2026',
          category: 'Monetary Policy Department',
          file_path: 'documents/cb-circ-2026-05.pdf',
          file_extension: 'pdf',
          status: 'COMPLETED',
          origin: 'MANUAL',
          source_url: null,
          uploaded_by_user_id: 'admin-1',
        };
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
