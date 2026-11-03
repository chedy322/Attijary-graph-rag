import { Component, ElementRef, OnInit, ViewChild, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, ActivatedRoute } from '@angular/router';
import { AgentService } from '../../core/services';
import { MarkdownComponent } from 'ngx-markdown';
import { Chat, Conversation, AgentQueryResponse, AgentStreamEvent } from '../../core/models';

@Component({
  selector: 'app-chat-interface',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, MarkdownComponent],
  templateUrl: './chat-interface.component.html',
  styleUrl: './chat-interface.component.scss',
})
export class ChatInterfaceComponent implements OnInit {
  @ViewChild('messagesViewport')
  private messagesViewport?: ElementRef<HTMLElement>;

  private agentService = inject(AgentService);
  private route = inject(ActivatedRoute);

  chats: Chat[] = [];
  activeChatId: string | null = null;
  activeChatTitle = 'New Chat Session';
  messages: Conversation[] = [];
  userPrompt = '';
  isThinking = false;
  activeTab: 'all' | 'today' | 'week' | 'older' = 'all';
  errorMessage: string | null = null;
  showChatHistory = false;

  toggleChatHistory(): void {
    this.showChatHistory = !this.showChatHistory;
  }

  ngOnInit(): void {
    this.route.params.subscribe((params) => {
      if (params['id']) {
        this.activeChatId = params['id'];
        this.loadChatMessages(params['id']);
      } else {
        this.loadChatSessions();
      }
    });
  }

  loadChatSessions(): void {
    this.agentService.getChats().subscribe({
      next: (res) => {
        if (res && res.chats && res.chats.length > 0) {
          this.chats = res.chats;
          if (!this.activeChatId) {
            this.selectChat(this.chats[0].chat_id);
           
          }
        } else {
          this.chats = [];
        }
      },
      error: (err) => {
        this.chats = [];
        this.messages = [];
        this.errorMessage = this.getErrorMessage(err, 'Unable to load chat sessions.');
      },
    });
  }

  selectChat(chatId: string): void {
    this.activeChatId = chatId;
    const chat = this.chats.find((c) => c.chat_id === chatId);
    if (chat) {
      this.activeChatTitle = chat.title || 'Conversation';
    }
    this.loadChatMessages(chatId);
  }

  createNewChat(): void {
    this.activeChatId = null;
    this.activeChatTitle = 'New Chat Session';
    this.messages = [];
  }
  onMarkdownReady(): void {
  this.scrollMessagesToBottom(false);
}

  loadChatMessages(chatId: string): void {
    this.errorMessage = null;
    this.agentService.getChatMessages(chatId).subscribe({
      next: (res) => {
        this.messages = res.messages;
        this.activeChatTitle = res.title || 'Conversation';
         this.scrollMessagesToBottom(true);
      },
      error: (err) => {
        this.messages = [];
        this.errorMessage = this.getErrorMessage(err, 'Unable to load this chat conversation.');
      },
    });
  }
  private scrollMessagesToBottom(force = false): void {
    setTimeout(() => {
     
      const viewport = this.messagesViewport?.nativeElement;
      if (!viewport) return;

      const distanceFromBottom =
        viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight;
      if (force || distanceFromBottom <= 120) {
        viewport.scrollTo({
          top: viewport.scrollHeight,
          behavior: force ? 'smooth' : 'auto',
        });
      }
    }, 50);
  }

sendQuery(): void {
  const queryText = this.userPrompt.trim();
  if (!queryText || this.isThinking) return;

  // 1. Add User Message
  this.messages.push({
    conversation_id: 'conv-' + Date.now(),
    chat_id: this.activeChatId || 'temp',
    role: 'USER',
    content: queryText,
    created_at: new Date().toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    }),
    rag_source: null,
  });

  this.userPrompt = '';
  this.isThinking = true; // Shows "Evaluating Vector Embeddings..."
  this.scrollMessagesToBottom(true);

  let placeholderAiMessage: Conversation | null = null;

  this.agentService
    .queryAgentStream({ query: queryText, chat_id: this.activeChatId })
    .subscribe({
      next: (event: AgentStreamEvent) => {
        if (event.type === 'chunk') {
          // On FIRST chunk token: hide thinking indicator and push assistant card
          if (this.isThinking) {
            this.isThinking = false;
            placeholderAiMessage = {
              conversation_id: 'stream-' + Date.now(),
              chat_id: this.activeChatId || 'temp',
              role: 'ASSISTANT',
              content: '',
              created_at: new Date().toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              }),
              rag_source: null,
            };
            this.messages.push(placeholderAiMessage);
          }

          if (placeholderAiMessage) {
            placeholderAiMessage.content += (event.data as string) || '';
            this.scrollMessagesToBottom();
          }
        } else if (event.type === 'complete') {
          this.isThinking = false;
          
          if (event.data) {
            const finalData = event.data as AgentQueryResponse;

            if (placeholderAiMessage) {
              // Update metadata & IDs from backend completion payload
              placeholderAiMessage.conversation_id = finalData.conversation_id || placeholderAiMessage.conversation_id;
              placeholderAiMessage.rag_source = finalData.rag_source || null;

              // Only assign content if stream was empty or backend returned complete response
              if (finalData.content && !placeholderAiMessage.content) {
                placeholderAiMessage.content = finalData.content;
              }
            }

            // Sync newly created chat session to component state
            if (!this.activeChatId && finalData.chat_id) {
              this.activeChatId = finalData.chat_id;
              this.loadChatSessions(); // Refresh sidebar session list
            }
          }

          this.scrollMessagesToBottom(true);
        }
      },
      error: (err) => {
        this.isThinking = false;
        this.errorMessage = this.getErrorMessage(err, 'Failed to fetch agent stream.');
        this.scrollMessagesToBottom(true);
      },
    });
}
  

  deleteChat(chatId: string, event: Event): void {
    event.stopPropagation();
    this.agentService.deleteChat(chatId).subscribe({
      next: () => {
        this.chats = this.chats.filter((chat) => chat.chat_id !== chatId);
        if (this.activeChatId === chatId) {
          this.activeChatId = null;
          this.messages = [];
          this.activeChatTitle = 'New Chat Session';
        }
      },
      error: (err) => {
        this.errorMessage = this.getErrorMessage(err, 'Unable to delete this chat.');
      },
    });
  }

  private getErrorMessage(error: unknown, fallback: string): string {
    const response = error as { error?: { message?: string }; message?: string };
    return response.error?.message || response.message || fallback;
  }

}
