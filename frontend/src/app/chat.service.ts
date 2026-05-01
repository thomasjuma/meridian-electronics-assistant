import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { map, Observable } from 'rxjs';
import { environment } from '../environments/environment';

const configuredApiBaseUrl = environment.apiBaseUrl?.trim();
const apiBaseUrl =
  configuredApiBaseUrl && configuredApiBaseUrl.length > 0
    ? configuredApiBaseUrl.replace(/\/+$/, '')
    : '/api';

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  session_id?: string;
  history?: ChatHistoryMessage[];
}

export interface ConversationResponse {
  session_id: string;
  messages: ChatHistoryMessage[];
}

export interface ChatHistoryMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

@Injectable({
  providedIn: 'root',
})
export class ChatService {
  private readonly chatEndpoint = `${apiBaseUrl}/chat`;
  private readonly conversationEndpoint = `${apiBaseUrl}/conversation`;

  constructor(private readonly http: HttpClient) {}

  private normalizeRole(role: unknown): 'user' | 'assistant' | undefined {
    const normalized = String(role ?? '')
      .trim()
      .toLowerCase();
    if (['user', 'human', 'customer'].includes(normalized)) {
      return 'user';
    }
    if (['assistant', 'ai', 'bot', 'agent', 'system'].includes(normalized)) {
      return 'assistant';
    }
    return undefined;
  }

  private normalizeHistory(rawHistory: unknown): ChatHistoryMessage[] | undefined {
    if (!Array.isArray(rawHistory)) {
      return undefined;
    }

    const messages: ChatHistoryMessage[] = [];
    for (const item of rawHistory) {
      if (typeof item !== 'object' || item === null) {
        continue;
      }

      const role = this.normalizeRole(item['role']);
      const content = String(item['content'] ?? '').trim();
      if (!role || content.length === 0) {
        continue;
      }

      messages.push({
        role,
        content,
        timestamp: typeof item['timestamp'] === 'string' ? item['timestamp'] : undefined,
      });
    }

    return messages.length > 0 ? messages : undefined;
  }

  sendMessage(payload: ChatRequest): Observable<ChatResponse> {
    return this.http.post<unknown>(this.chatEndpoint, payload).pipe(
      map((raw) => {
        const parsed = (raw ?? {}) as Record<string, unknown>;
        const responseText = [
          parsed['response'],
          parsed['assistant_response'],
          parsed['answer'],
          parsed['message'],
        ].find((value) => typeof value === 'string' && String(value).trim().length > 0);

        return {
          response: String(responseText ?? ''),
          session_id:
            typeof parsed['session_id'] === 'string' ? parsed['session_id'] : undefined,
          history: this.normalizeHistory(parsed['history'] ?? parsed['messages']),
        };
      }),
    );
  }

  loadConversation(sessionId: string): Observable<ConversationResponse> {
    return this.http.get<unknown>(`${this.conversationEndpoint}/${sessionId}`).pipe(
      map((raw) => {
        const parsed = (raw ?? {}) as Record<string, unknown>;
        return {
          session_id: String(parsed['session_id'] ?? sessionId),
          messages: this.normalizeHistory(parsed['messages'] ?? parsed['history']) ?? [],
        };
      }),
    );
  }
}
