import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, ActivatedRoute } from '@angular/router';
import { AgentService } from '../../core/services';
import { Chat, Conversation, AgentQueryResponse } from '../../core/models';

@Component({
  selector: 'app-chat-interface',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './chat-interface.component.html',
  styleUrl: './chat-interface.component.scss',
})
export class ChatInterfaceComponent implements OnInit {
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

  loadChatMessages(chatId: string): void {
    this.errorMessage = null;
    this.agentService.getChatMessages(chatId).subscribe({
      next: (res) => {
        this.messages = res.messages;
        this.activeChatTitle = res.title || 'Conversation';
      },
      error: (err) => {
        this.messages = [];
        this.errorMessage = this.getErrorMessage(err, 'Unable to load this chat conversation.');
      },
    });
  }

  sendQuery(): void {
    if (!this.userPrompt.trim() || this.isThinking) return;

    const query = this.userPrompt;
    this.userPrompt = '';
    this.errorMessage = null;

    // Push User message turn
    const userMsg: Conversation = {
      conversation_id: 'conv-' + Date.now(),
      chat_id: this.activeChatId || 'temp',
      role: 'USER',
      content: query,
      created_at: new Date().toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      }),
      rag_source: null,
    };
    this.messages.push(userMsg);
    this.isThinking = true;

    this.agentService
      .queryAgent({
        chat_id: this.activeChatId,
        query: query,
      })
      .subscribe({
        next: (res: AgentQueryResponse) => {
          this.isThinking = false;
          if (!this.activeChatId) {
            this.activeChatId = res.chat_id;
          }
          const assistantMsg: Conversation = {
            conversation_id: res.conversation_id,
            chat_id: res.chat_id,
            role: 'ASSISTANT',
            content: res.content,
            created_at: res.created_at,
            rag_source: res.rag_source,
          };
          this.messages.push(assistantMsg);
        },
        error: (err) => {
          this.isThinking = false;
          this.errorMessage = this.getErrorMessage(err, 'Unable to process your query.');
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
