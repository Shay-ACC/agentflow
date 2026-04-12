export type ApiHealth = {
  status: string;
  environment: string;
  services: {
    database: {
      ready: boolean;
      error: string | null;
    };
    redis: {
      configured: boolean;
      ready: boolean;
      url: string;
      error: string | null;
    };
    qdrant: {
      configured: boolean;
      ready: boolean;
      url: string;
      error: string | null;
    };
    llm: {
      configured: boolean;
      provider: string;
      model: string;
    };
  };
};

export type Conversation = {
  id: number;
  created_at: string;
};

export type MessageRole = "user" | "assistant" | "system";

export type Message = {
  id: number;
  conversation_id: number;
  role: MessageRole;
  content: string;
  created_at: string;
};

export type CreateMessageResult = {
  user_message: Message;
  assistant_message: Message;
};

export type ApiRequestOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  headers?: Record<string, string>;
};

export type CreateMessageInput = {
  role: MessageRole;
  content: string;
};
