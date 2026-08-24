import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { AgentService } from '../../core/services';
import { GraphLineageResponse } from '../../core/models';

@Component({
  selector: 'app-graph-explorer',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './graph-explorer.component.html',
  styleUrl: './graph-explorer.component.scss',
})
export class GraphExplorerComponent implements OnInit {
  private agentService = inject(AgentService);

  documentId = 'cb-circ-2026-05';
  graphData: GraphLineageResponse | null = null;
  selectedTab: 'details' | 'relationships' = 'details';

  // Active selected node details
  selectedNode = {
    title: 'Circular N° 2026-05',
    subtitle: 'Reserve Requirements',
    fullTitle: 'Reserve Requirements for Commercial Banks in Local Currency',
    documentId: 'CB-CIRC-2026-05',
    dateIssued: 'May 15, 2026',
    category: 'Monetary Policy',
    subCategory: 'Reserve Requirements',
    origin: 'Monetary Policy Department',
    status: 'Current',
    version: '1.0',
    language: 'English',
    summary:
      'This circular sets out the reserve requirements applicable to all commercial banks for their local currency liabilities.',
  };

  ngOnInit(): void {
    this.loadGraphData();
  }

  loadGraphData(): void {
    this.agentService.getGraphLineage(this.documentId).subscribe({
      next: (data) => {
        this.graphData = data;
      },
      error: () => {
        // Fallback mock graph nodes matching Mockup 2
        this.graphData = {
          root_document_id: 'cb-circ-2026-05',
          nodes: [
            {
              id: 'cb-circ-2026-05',
              label: 'Circular N° 2026-05',
              type: 'Document',
            },
            {
              id: 'cb-circ-2024-08',
              label: 'Circular N° 2024-08',
              type: 'Document',
            },
            {
              id: 'cb-circ-2022-12',
              label: 'Circular N° 2022-12',
              type: 'Document',
            },
            {
              id: 'reg-2019',
              label: 'Regulation Act 2019',
              type: 'Regulation',
            },
            {
              id: 'cb-circ-2021-07',
              label: 'Circular N° 2021-07',
              type: 'Document',
            },
            {
              id: 'cb-circ-2020-11',
              label: 'Circular N° 2020-11',
              type: 'Document',
            },
            {
              id: 'cb-circ-2023-03',
              label: 'Circular N° 2023-03',
              type: 'Document',
            },
            {
              id: 'cb-circ-2025-01',
              label: 'Circular N° 2025-01',
              type: 'Document',
            },
          ],
          edges: [
            {
              source: 'cb-circ-2026-05',
              target: 'cb-circ-2024-08',
              relationship: 'REFERENCES',
            },
            {
              source: 'cb-circ-2026-05',
              target: 'cb-circ-2022-12',
              relationship: 'MODIFIES',
            },
            {
              source: 'cb-circ-2026-05',
              target: 'reg-2019',
              relationship: 'DERIVED FROM',
            },
            {
              source: 'cb-circ-2026-05',
              target: 'cb-circ-2021-07',
              relationship: 'REFERENCES',
            },
            {
              source: 'cb-circ-2026-05',
              target: 'cb-circ-2020-11',
              relationship: 'RELATED TO',
            },
            {
              source: 'cb-circ-2026-05',
              target: 'cb-circ-2023-03',
              relationship: 'REFERENCES',
            },
            {
              source: 'cb-circ-2026-05',
              target: 'cb-circ-2025-01',
              relationship: 'REFERENCES',
            },
          ],
        };
      },
    });
  }

  selectNode(nodeId: string, label: string): void {
    this.selectedNode.title = label;
    this.selectedNode.documentId = nodeId.toUpperCase();
  }
}
