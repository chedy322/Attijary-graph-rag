import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { AuthService } from './auth.service';
import { environment } from '../../../environments/environment';
import {
  AgentQueryRequest,
  AgentQueryResponse,
  AgentStreamEvent,
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
  private authService = inject(AuthService);
  private baseUrl = `${environment.apiUrl}/v1/agent`;

  /**
   * Main execution route for natural language interaction with LangGraph + Hybrid Search + GraphRAG.
   */
  queryAgent(request: AgentQueryRequest): Observable<AgentQueryResponse> {
    return this.http.post<AgentQueryResponse>(`${this.baseUrl}/query`, request);
  }

  queryAgentStream(request: AgentQueryRequest): Observable<AgentStreamEvent> {
    return new Observable<AgentStreamEvent>((subscriber) => {
      const controller = new AbortController();
      const run = async () => {
        try {
          const token = await this.authService.getClerkToken();
          const response = await fetch(`${this.baseUrl}/query`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify(request),
            signal: controller.signal,
          });
          if (!response.ok || !response.body) {
            throw new Error(`Agent request failed (${response.status}).`);
          }

          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';

          const processCompleteLines = () => {
            const lines = buffer.split(/\r?\n/);
            buffer = lines.pop() || '';
            for (const line of lines) {
              this.emitStreamEvent(line, subscriber);
            }
          };

          while (true) {
            const result = await reader.read();
            if (result.done) {
              buffer += decoder.decode();
              processCompleteLines();
              if (buffer.trim()) {
                this.emitStreamEvent(buffer, subscriber);
              }
              break;
            }
            buffer += decoder.decode(result.value, { stream: true });
            processCompleteLines();
          }
          subscriber.complete();
        } catch (error) {
          if (!controller.signal.aborted) subscriber.error(error);
        }
      };
      void run();
      return () => controller.abort();
    });
  }

  private emitStreamEvent(
    line: string,
    subscriber: {
      next: (event: AgentStreamEvent) => void;
      error: (error: unknown) => void;
    },
  ): void {
    if (!line.trim()) return;

    try {
      const event = JSON.parse(line) as AgentStreamEvent;
      if (event.type === 'chunk' || event.type === 'complete' || event.type === 'error') {
        subscriber.next(event);
      }
    } catch (error) {
      subscriber.error(new Error(`Invalid agent stream event: ${String(error)}`));
    }
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
