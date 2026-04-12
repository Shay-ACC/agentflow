"use client";

import { useEffect, useState } from "react";

import { ChatThread } from "@/components/chat/chat-thread";
import { ConversationList } from "@/components/chat/conversation-list";
import { apiClient } from "@/lib/api";
import type { Conversation, Message } from "@/lib/api";


export function ChatWorkspace() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [isLoadingConversations, setIsLoadingConversations] = useState(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isCreatingConversation, setIsCreatingConversation] = useState(false);
  const [isSendingMessage, setIsSendingMessage] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;

    async function loadConversations() {
      setIsLoadingConversations(true);

      try {
        const nextConversations = await apiClient.listConversations();
        if (!isActive) {
          return;
        }

        setConversations(nextConversations);
        setSelectedConversationId((currentConversationId) => {
          if (
            currentConversationId !== null &&
            nextConversations.some(
              (conversation) => conversation.id === currentConversationId,
            )
          ) {
            return currentConversationId;
          }

          return nextConversations[0]?.id ?? null;
        });
        setError(null);
      } catch (nextError) {
        if (!isActive) {
          return;
        }

        setError(
          nextError instanceof Error
            ? nextError.message
            : "Failed to load conversations.",
        );
      } finally {
        if (isActive) {
          setIsLoadingConversations(false);
        }
      }
    }

    void loadConversations();

    return () => {
      isActive = false;
    };
  }, []);

  useEffect(() => {
    if (selectedConversationId === null) {
      setMessages([]);
      return;
    }

    let isActive = true;

    async function loadMessages() {
      setIsLoadingMessages(true);

      try {
        const nextMessages = await apiClient.listMessages(selectedConversationId);
        if (!isActive) {
          return;
        }

        setMessages(nextMessages);
        setError(null);
      } catch (nextError) {
        if (!isActive) {
          return;
        }

        setError(
          nextError instanceof Error
            ? nextError.message
            : "Failed to load messages.",
        );
      } finally {
        if (isActive) {
          setIsLoadingMessages(false);
        }
      }
    }

    void loadMessages();

    return () => {
      isActive = false;
    };
  }, [selectedConversationId]);

  const selectedConversation =
    conversations.find((conversation) => conversation.id === selectedConversationId) ?? null;

  async function handleCreateConversation() {
    setIsCreatingConversation(true);

    try {
      const conversation = await apiClient.createConversation();
      setConversations((currentConversations) => [conversation, ...currentConversations]);
      setSelectedConversationId(conversation.id);
      setMessages([]);
      setDraft("");
      setError(null);
    } catch (nextError) {
      setError(
        nextError instanceof Error
          ? nextError.message
          : "Failed to create a conversation.",
      );
    } finally {
      setIsCreatingConversation(false);
    }
  }

  async function handleSendMessage() {
    const content = draft.trim();
    if (selectedConversationId === null || content.length === 0) {
      return;
    }

    setIsSendingMessage(true);

    try {
      await apiClient.createMessage(selectedConversationId, {
        role: "user",
        content,
      });
      const nextMessages = await apiClient.listMessages(selectedConversationId);
      setMessages(nextMessages);
      setDraft("");
      setError(null);
    } catch (nextError) {
      setError(
        nextError instanceof Error
          ? nextError.message
          : "Failed to send the message.",
      );
    } finally {
      setIsSendingMessage(false);
    }
  }

  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <p className="text-sm uppercase tracking-[0.3em] text-app-muted">
          Chat
        </p>
        <h1 className="text-3xl font-semibold tracking-tight text-app-text">
          Conversation Workspace
        </h1>
        <p className="max-w-3xl text-sm leading-7 text-app-subtle">
          First frontend integration slice: create conversations, inspect stored
          messages, and send new user messages against the working backend CRUD
          endpoints.
        </p>
      </header>

      {error ? (
        <div className="rounded-2xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
          {error}
        </div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[320px_minmax(0,1fr)]">
        <ConversationList
          conversations={conversations}
          selectedConversationId={selectedConversationId}
          isLoading={isLoadingConversations}
          isCreating={isCreatingConversation}
          onCreateConversation={handleCreateConversation}
          onSelectConversation={setSelectedConversationId}
        />

        <ChatThread
          conversation={selectedConversation}
          messages={messages}
          draft={draft}
          isLoadingMessages={isLoadingMessages}
          isSendingMessage={isSendingMessage}
          onDraftChange={setDraft}
          onSendMessage={handleSendMessage}
          onCreateConversation={handleCreateConversation}
        />
      </div>
    </section>
  );
}
