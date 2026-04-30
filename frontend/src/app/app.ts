import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { finalize } from 'rxjs';
import { ChatService } from './chat.service';

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
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (response) => {
          this.sessionId = response.session_id;
          this.messages.push({
            role: 'assistant',
            content: response.response,
          });
        },
        error: () => {
          this.errorMessage = 'Unable to reach the chat service. Please try again.';
        },
      });
  }
}
