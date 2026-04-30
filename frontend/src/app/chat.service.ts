import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
}

@Injectable({
  providedIn: 'root',
})
export class ChatService {
  private readonly chatEndpoint = '/api/chat';

  constructor(private readonly http: HttpClient) {}

  sendMessage(payload: ChatRequest): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(this.chatEndpoint, payload);
  }
}
