import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, ActivatedRoute } from '@angular/router';
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
  private route = inject(ActivatedRoute);

  documentId = '';
  graphData: GraphLineageResponse | null = null;
  selectedTab: 'details' | 'relationships' = 'details';

  // Active selected node details
  selectedNode = {
    title: '',
    subtitle: '',
    fullTitle: '',
    documentId: '',
    dateIssued: '',
    category: '',
    subCategory: '',
    origin: '',
    status: '',
    version: '',
    language: '',
    summary: '',
  };

  ngOnInit(): void {
    const documentId = this.route.snapshot.paramMap.get('documentId');
    if (documentId) {
      this.documentId = documentId;
      this.loadGraphData();
    } else {
      this.errorMessage = 'Select a document to view its graph lineage.';
    }
  }

  errorMessage: string | null = null;

  loadGraphData(): void {
    this.errorMessage = null;
    this.agentService.getGraphLineage(this.documentId).subscribe({
      next: (data) => {
        this.graphData = data;
      },
      error: (err) => {
        this.errorMessage = err?.error?.message || err?.message || 'Failed to load graph lineage from Neo4j service.';
        this.graphData = null;
      },
    });
  }

  selectNode(nodeId: string, label: string): void {
    this.selectedNode.title = label;
    this.selectedNode.documentId = nodeId.toUpperCase();
  }
}
