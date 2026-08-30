import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  AgentQueryRequest,
  AgentQueryResponse,
  Chat,
  ChatListResponse,
  ChatMessagesResponse,
  DeleteChatResponse,
} from '../models/chat.model';
import { GraphLineageResponse } from '../models/graph.model';

@Injectable({
  providedIn: 'root',
})
export class AgentService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrl}/v1/agent`;

  /**
   * Main execution route for natural language interaction with LangGraph + Hybrid Search + GraphRAG.
   */
  queryAgent(request: AgentQueryRequest): Observable<AgentQueryResponse> {
    return this.http.post<AgentQueryResponse>(`${this.baseUrl}/query`, request);
  }

  /**
   * Fetches all chat sessions/threads created by the authenticated user.
   */
  getChats(): Observable<ChatListResponse> {
    return this.http.get<Chat[]>(`${this.baseUrl}/chats`).pipe(
      map((chats) => ({ chats })),
    );
  }

  /**
   * Retrieves the complete list of message turns for a specific chat thread.
   */
  getChatMessages(chatId: string): Observable<ChatMessagesResponse> {
    return this.http.get<ChatMessagesResponse>(
      `${this.baseUrl}/chats/${chatId}/messages`,
    );
  }

  /**
   * Deletes a chat session and cascades to delete all associated message rows.
   */
  deleteChat(chatId: string): Observable<DeleteChatResponse> {
    return this.http.delete<DeleteChatResponse>(
      `${this.baseUrl}/chats/${chatId}`,
    );
  }

  /**
   * Fetches structural graph connections (nodes and edges) associated with a given document.
   */
  getGraphLineage(documentId: string): Observable<GraphLineageResponse> {
    return this.http.get<GraphLineageResponse>(
      `${this.baseUrl}/graph/lineage/${documentId}`,
    );
  }
}
