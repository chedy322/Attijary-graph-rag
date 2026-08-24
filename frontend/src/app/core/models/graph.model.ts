export interface GraphNode {
  id: string;
  label: string;
  type: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
}

export interface GraphLineageResponse {
  root_document_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}
