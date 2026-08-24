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
  activeChatTitle = 'Reserve requirements';
  messages: Conversation[] = [];
  userPrompt = '';
  isThinking = false;
  activeTab: 'all' | 'today' | 'week' | 'older' = 'all';

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
          this.loadMockSessions();
        }
      },
      error: () => {
        this.loadMockSessions();
      },
    });
  }

  private loadMockSessions(): void {
    this.chats = [
      {
        chat_id: 'chat-1',
        user_id: 'user-1',
        created_at: '10:24 AM',
        title: 'Reserve requirements',
      },
      {
        chat_id: 'chat-2',
        user_id: 'user-1',
        created_at: 'Yesterday',
        title: 'Anti-Money Laundering (AML)',
      },
      {
        chat_id: 'chat-3',
        user_id: 'user-1',
        created_at: 'Yesterday',
        title: 'Capital Adequacy Ratio (CAR)',
      },
      {
        chat_id: 'chat-4',
        user_id: 'user-1',
        created_at: 'Jun 1',
        title: 'Liquidity Coverage Ratio (LCR)',
      },
      {
        chat_id: 'chat-5',
        user_id: 'user-1',
        created_at: 'May 30',
        title: 'KYC Requirements',
      },
      {
        chat_id: 'chat-6',
        user_id: 'user-1',
        created_at: 'May 29',
        title: 'Stress Testing Guidelines',
      },
      {
        chat_id: 'chat-7',
        user_id: 'user-1',
        created_at: 'May 28',
        title: 'Foreign Exchange Controls',
      },
    ];
    if (!this.activeChatId) {
      this.selectChat('chat-1');
    }
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
    this.agentService.getChatMessages(chatId).subscribe({
      next: (res) => {
        if (res && res.messages && res.messages.length > 0) {
          this.messages = res.messages;
        } else {
          this.loadMockMessages();
        }
      },
      error: () => {
        this.loadMockMessages();
      },
    });
  }

  private loadMockMessages(): void {
    this.messages = [
      {
        conversation_id: 'conv-1',
        chat_id: this.activeChatId || 'chat-1',
        role: 'USER',
        content:
          'What are the current reserve requirements for commercial banks in local currency?',
        created_at: '10:24 AM',
        rag_source: null,
      },
      {
        conversation_id: 'conv-2',
        chat_id: this.activeChatId || 'chat-1',
        role: 'ASSISTANT',
        content:
          'According to the Central Bank regulations, the current reserve requirements for commercial banks in local currency are as follows:\n\n• Demand deposits: 10% of the total amount\n• Time and savings deposits: 5% of the total amount\n• These requirements are applicable to all banks licensed by the Central Bank.\n\nBanks must maintain these reserves in eligible accounts with the Central Bank on a daily average basis.',
        created_at: '10:24 AM',
        rag_source: {
          confidence_score: 88.5,
          sources: [
            {
              document_id: 'cb-circ-2026-05',
              document: 'Circular_2026_05_Reserve_Req.pdf',
              title: 'Circular N° 2026-05 on Reserve Requirements',
              page: 4,
              snippet:
                'Banks must maintain reserve balances in eligible accounts with the Central Bank...',
            },
            {
              document_id: 'cb-circ-2022-12',
              document: 'Circular_2022_12_Reserve_Req.pdf',
              title: 'Circular N° 2022-12 on Reserve Requirements',
              page: 1,
              snippet: 'Prior reserve requirement standards...',
            },
            {
              document_id: 'cb-manual',
              document: 'Reserve_Requirements_Manual.pdf',
              title: 'Reserve Requirements Compliance Manual',
              page: 12,
              snippet: 'Operational compliance procedures...',
            },
          ],
          graph_context: [
            {
              source_node: 'Circular N° 2026-05',
              relationship: 'MODIFIES',
              target_node: 'Circular N° 2022-12',
              graph_path: '(Circular 2026-05)-[:MODIFIES]->(Circular 2022-12)',
            },
          ],
        },
      },
    ];
  }

  sendQuery(): void {
    if (!this.userPrompt.trim() || this.isThinking) return;

    const query = this.userPrompt;
    this.userPrompt = '';

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
        error: () => {
          // Fallback response for demo
          setTimeout(() => {
            this.isThinking = false;
            const assistantMsg: Conversation = {
              conversation_id: 'conv-' + Date.now(),
              chat_id: this.activeChatId || 'chat-1',
              role: 'ASSISTANT',
              content: `Based on Central Bank Circulars and Neo4j Graph analysis, your query regarding "${query}" relates directly to regulatory compliance standards established under Circular N° 2026-05.`,
              created_at: new Date().toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              }),
              rag_source: {
                confidence_score: 92.0,
                sources: [
                  {
                    document_id: 'cb-circ-2026-05',
                    document: 'Circular_2026_05_Reserve_Req.pdf',
                    title: 'Circular N° 2026-05',
                    page: 3,
                    snippet: 'Mandatory ratios...',
                  },
                ],
                graph_context: [
                  {
                    source_node: 'Circular N° 2026-05',
                    relationship: 'MODIFIES',
                    target_node: 'Circular N° 2022-12',
                  },
                ],
              },
            };
            this.messages.push(assistantMsg);
          }, 1200);
        },
      });
  }
}
