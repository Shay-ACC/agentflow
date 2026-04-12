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

export type DocumentRecord = {
  id: number;
  filename: string;
  content_type: string | null;
  byte_size: number;
  text_length: number;
  chunk_count: number;
  index_status: "indexed" | "index_missing";
  created_at: string;
};

export type DocumentUploadResult = {
  document: DocumentRecord;
  deduplicated: boolean;
};

export type MessageRole = "user" | "assistant" | "system";

export type Message = {
  id: number;
  conversation_id: number;
  role: MessageRole;
  content: string;
  created_at: string;
};

export type RunStatus = "pending" | "completed" | "failed";

export type Run = {
  id: number;
  conversation_id: number;
  user_message_id: number;
  user_message_preview: string;
  provider: string;
  model: string;
  status: RunStatus;
  error_message: string | null;
  started_at: string;
  finished_at: string | null;
};

export type RunSource = {
  document_id: number;
  chunk_id: number;
  chunk_index: number;
  rank: number;
  content_preview: string;
};

export type RunDetail = Run & {
  sources: RunSource[];
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
