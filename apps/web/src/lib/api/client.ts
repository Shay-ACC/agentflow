import { env } from "@/lib/env";

import type {
  ApiHealth,
  ApiRequestOptions,
  Conversation,
  CreateMessageInput,
  Message,
} from "./types";


export class ApiClient {
  constructor(private readonly baseUrl: string) {}

  buildUrl(path: string): string {
    return new URL(path, this.baseUrl).toString();
  }

  async request<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
    const response = await fetch(this.buildUrl(path), {
      method: options.method ?? "GET",
      headers: {
        ...(options.body === undefined ? {} : { "Content-Type": "application/json" }),
        ...options.headers,
      },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      cache: "no-store",
    });

    if (!response.ok) {
      const errorPayload = (await response.json().catch(() => null)) as
        | { detail?: string }
        | null;
      throw new Error(errorPayload?.detail ?? "Request failed.");
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return (await response.json()) as T;
  }

  async getHealth(): Promise<ApiHealth> {
    return this.request<ApiHealth>("/health");
  }

  async listConversations(): Promise<Conversation[]> {
    return this.request<Conversation[]>("/conversations");
  }

  async getConversation(conversationId: number): Promise<Conversation> {
    return this.request<Conversation>(`/conversations/${conversationId}`);
  }

  async createConversation(): Promise<Conversation> {
    return this.request<Conversation>("/conversations", {
      method: "POST",
      body: {},
    });
  }

  async listMessages(conversationId: number): Promise<Message[]> {
    return this.request<Message[]>(`/conversations/${conversationId}/messages`);
  }

  async createMessage(
    conversationId: number,
    payload: CreateMessageInput,
  ): Promise<Message> {
    return this.request<Message>(`/conversations/${conversationId}/messages`, {
      method: "POST",
      body: payload,
    });
  }
}


export const apiClient = new ApiClient(env.apiBaseUrl);
