import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { AgentService } from '../../core/services';
import { GraphLineageResponse, GraphNode } from '../../core/models';

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

  documentId = 'cb-circ-2026-05';
  graphData: GraphLineageResponse | null = null;
  selectedNode: GraphNode | null = null;
  isLoading = false;
  errorMessage: string | null = null;
  selectedTab: 'details' | 'relationships' = 'details';

  ngOnInit(): void {
    this.route.paramMap.subscribe((params) => {
      const routeDocumentId = params.get('documentId');
      const queryDocumentId = this.route.snapshot.queryParamMap.get('document_id');
      const nextDocumentId = routeDocumentId ?? queryDocumentId ?? this.documentId;

      if (nextDocumentId) {
        this.documentId = nextDocumentId;
      }

      this.loadGraphData();
    });
  }

  loadGraphData(): void {
    this.isLoading = true;
    this.errorMessage = null;
    this.agentService.getGraphLineage(this.documentId).subscribe({
      next: (data) => {
        this.graphData = data;
        this.selectedNode =
          data.nodes.find((node) => node.id === data.root_document_id) ??
          data.nodes[0] ??
          null;
        this.isLoading = false;
      },
      error: () => {
        this.graphData = null;
        this.selectedNode = null;
        this.isLoading = false;
        this.errorMessage = 'Unable to load graph lineage for this document.';
      },
    });
  }

  selectNode(nodeOrId: GraphNode | string, label?: string): void {
    if (typeof nodeOrId !== 'string') {
      this.selectedNode = nodeOrId;
      return;
    }

    const node = this.graphData?.nodes.find((item) => item.id === nodeOrId);
    this.selectedNode = node ?? {
      id: nodeOrId,
      label: label ?? nodeOrId,
      type: 'Document',
    };
  }

  getNodePosition(index: number): string {
    return [
      'node-top',
      'node-top-right',
      'node-right',
      'node-bottom-right',
      'node-bottom',
      'node-bottom-left',
      'node-left',
    ][index - 1] ?? 'node-bottom';
  }

  getNodeLabel(nodeId: string): string {
    return this.graphData?.nodes.find((node) => node.id === nodeId)?.label ?? nodeId;
  }

  getOutgoingEdges(nodeId: string) {
    return this.graphData?.edges.filter((edge) => edge.source === nodeId) ?? [];
  }
}
