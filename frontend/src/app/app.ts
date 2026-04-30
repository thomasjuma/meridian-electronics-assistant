import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { ChatService } from './chat.service';
import { marked } from 'marked';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

@Component({
  selector: 'app-root',
  imports: [CommonModule, FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  sessionId = '';
  prompt = '';
  isLoading = false;
  errorMessage = '';
  messages: ChatMessage[] = [
    {
      role: 'assistant',
      content: 'Hello! Ask me anything about your order and I can help.',
    },
  ];

  constructor(private readonly chatService: ChatService) {}

  renderMarkdown(content: string): string {
    const source = typeof content === 'string' ? content : '';
    const parsed = marked.parse(source, { async: false, breaks: true });
    const html = typeof parsed === 'string' ? parsed : '';
    const plainText = html.replace(/<[^>]*>/g, '').trim();

    if (plainText.length === 0 && source.trim().length > 0) {
      return `<p>${this.escapeHtml(source)}</p>`;
    }

    return html;
  }

  private escapeHtml(value: string): string {
    return value
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }

  sendOnEnter(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  sendMessage(): void {
    const message = this.prompt.trim();
    if (!message || this.isLoading) {
      return;
    }

    this.messages.push({ role: 'user', content: message });
    this.prompt = '';
    this.errorMessage = '';
    this.isLoading = true;

    this.chatService
      .sendMessage({
        message,
        session_id: this.sessionId || undefined,
      })
      .subscribe({
        next: (response) => {
          try {
            if (response.session_id) {
              this.sessionId = response.session_id;
            }

            const historyMessages = (response.history ?? []).map(({ role, content }) => ({
              role,
              content,
            }));

            if (historyMessages.length > 0) {
              this.messages = historyMessages;
              return;
            }

            this.messages.push({
              role: 'assistant',
              content: response.response || 'I did not receive a response. Please try again.',
            });
          } finally {
            this.isLoading = false;
          }
        },
        error: (error: HttpErrorResponse) => {
          const detail =
            typeof error.error?.detail === 'string' ? error.error.detail : undefined;
          this.errorMessage =
            detail || 'Unable to reach the chat service. Please try again.';
          this.isLoading = false;
        },
      });
  }
}
