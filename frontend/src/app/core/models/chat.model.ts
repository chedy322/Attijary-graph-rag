export type MessageRole = 'USER' | 'ASSISTANT' | 'SYSTEM';

export interface Chat {
  chat_id: string;
  user_id: string;
  created_at: string;
  title: string | null;
}

export interface RagSourceItem {
  document_id?: string;
  document?: string;
  title?: string;
  number?: string;
  page?: number;
  page_number?: number;
  snippet?: string;
  extracted_from?: string;
  circular_dependency_detected?: boolean;
  graph_path?: string;
}

export interface RagGraphContextItem {
  source_node: string;
  relationship: string;
  target_node: string;
  graph_path?: string;
}

export interface RagSource {
  confidence_score: number;
  sources: RagSourceItem[];
  graph_context?: RagGraphContextItem[];
}

export interface Conversation {
  conversation_id: string;
  chat_id: string;
  role: MessageRole;
  content: string;
  created_at: string;
  rag_source: RagSource | null;
}

export interface AgentQueryRequest {
  chat_id: string | null;
  query: string;
}

export interface AgentQueryResponse {
  chat_id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  created_at: string;
  rag_source: RagSource;
}

export interface ChatListResponse {
  chats: Chat[];
}

export interface ChatMessagesResponse {
  chat_id: string;
  title: string;
  messages: Conversation[];
}

export interface DeleteChatResponse {
  message: string;
  chat_id: string;
}
