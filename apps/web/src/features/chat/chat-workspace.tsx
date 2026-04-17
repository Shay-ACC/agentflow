"use client";

import { useEffect, useState } from "react";

import { ChatThread } from "@/components/chat/chat-thread";
import { ConversationList } from "@/components/chat/conversation-list";
import { apiClient } from "@/lib/api";
import type { Conversation, Message, Run, RunDetail } from "@/lib/api";


export function ChatWorkspace() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [selectedRun, setSelectedRun] = useState<RunDetail | null>(null);
  const [draft, setDraft] = useState("");
  const [isLoadingConversations, setIsLoadingConversations] = useState(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isLoadingRuns, setIsLoadingRuns] = useState(false);
  const [isLoadingRunDetail, setIsLoadingRunDetail] = useState(false);
  const [isCreatingConversation, setIsCreatingConversation] = useState(false);
  const [deletingConversationId, setDeletingConversationId] = useState<number | null>(null);
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

  useEffect(() => {
    if (selectedConversationId === null) {
      setRuns([]);
      setSelectedRunId(null);
      setSelectedRun(null);
      return;
    }

    let isActive = true;

    async function loadRuns() {
      setIsLoadingRuns(true);

      try {
        const nextRuns = await apiClient.listRuns(selectedConversationId);
        if (!isActive) {
          return;
        }

        setRuns(nextRuns);
        setSelectedRunId((currentRunId) => {
          if (currentRunId !== null && nextRuns.some((run) => run.id === currentRunId)) {
            return currentRunId;
          }

          return null;
        });
        setError(null);
      } catch (nextError) {
        if (!isActive) {
          return;
        }

        setError(
          nextError instanceof Error
            ? nextError.message
            : "Failed to load runs.",
        );
      } finally {
        if (isActive) {
          setIsLoadingRuns(false);
        }
      }
    }

    void loadRuns();

    return () => {
      isActive = false;
    };
  }, [selectedConversationId]);

  useEffect(() => {
    if (selectedRunId === null) {
      setSelectedRun(null);
      return;
    }

    let isActive = true;

    async function loadRunDetail() {
      setIsLoadingRunDetail(true);

      try {
        const nextRun = await apiClient.getRun(selectedRunId);
        if (!isActive) {
          return;
        }

        setSelectedRun(nextRun);
        setError(null);
      } catch (nextError) {
        if (!isActive) {
          return;
        }

        setSelectedRun(null);
        setError(
          nextError instanceof Error
            ? nextError.message
            : "Failed to load run detail.",
        );
      } finally {
        if (isActive) {
          setIsLoadingRunDetail(false);
        }
      }
    }

    void loadRunDetail();

    return () => {
      isActive = false;
    };
  }, [selectedRunId]);

  const selectedConversation =
    conversations.find((conversation) => conversation.id === selectedConversationId) ?? null;

  async function handleCreateConversation() {
    setIsCreatingConversation(true);

    try {
      const conversation = await apiClient.createConversation();
      setConversations((currentConversations) => [conversation, ...currentConversations]);
      setSelectedConversationId(conversation.id);
      setMessages([]);
      setRuns([]);
      setSelectedRunId(null);
      setSelectedRun(null);
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

  async function handleDeleteConversation(conversationId: number) {
    const conversation = conversations.find((item) => item.id === conversationId);
    if (conversation === undefined) {
      return;
    }

    const confirmed = window.confirm(
      `Delete Conversation ${conversation.id}? This will remove its messages and runs.`,
    );
    if (!confirmed) {
      return;
    }

    setDeletingConversationId(conversationId);

    try {
      await apiClient.deleteConversation(conversationId);

      const nextConversations = conversations.filter((item) => item.id !== conversationId);
      const isDeletingSelectedConversation = selectedConversationId === conversationId;

      setConversations(nextConversations);

      if (isDeletingSelectedConversation) {
        setSelectedConversationId(nextConversations[0]?.id ?? null);
        setMessages([]);
        setRuns([]);
        setSelectedRunId(null);
        setSelectedRun(null);
        setDraft("");
      }

      setError(null);
    } catch (nextError) {
      setError(
        nextError instanceof Error
          ? nextError.message
          : "Failed to delete the conversation.",
      );
    } finally {
      setDeletingConversationId(null);
    }
  }

  async function handleSendMessage() {
    const content = draft.trim();
    if (selectedConversationId === null || content.length === 0) {
      return;
    }

    setIsSendingMessage(true);

    try {
      const result = await apiClient.createMessage(selectedConversationId, {
        role: "user",
        content,
      });
      const nextRuns = await apiClient.listRuns(selectedConversationId);
      setMessages((currentMessages) => [
        ...currentMessages,
        result.user_message,
        result.assistant_message,
      ]);
      setRuns(nextRuns);
      setSelectedRunId(nextRuns[0]?.id ?? null);
      setDraft("");
      setError(null);
    } catch (nextError) {
      try {
        const nextMessages = await apiClient.listMessages(selectedConversationId);
        setMessages(nextMessages);
      } catch {
        // Keep the original request error when the recovery refresh also fails.
      }

      try {
        const nextRuns = await apiClient.listRuns(selectedConversationId);
        setRuns(nextRuns);
        setSelectedRunId(nextRuns[0]?.id ?? null);
      } catch {
        // Keep the original request error when the recovery refresh also fails.
      }

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
          First AI response slice: create conversations, send a user message,
          and render the saved assistant reply returned by the backend.
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
          deletingConversationId={deletingConversationId}
          onCreateConversation={handleCreateConversation}
          onSelectConversation={setSelectedConversationId}
          onDeleteConversation={handleDeleteConversation}
        />

        <ChatThread
          conversation={selectedConversation}
          messages={messages}
          runs={runs}
          selectedRun={selectedRun}
          draft={draft}
          isLoadingMessages={isLoadingMessages}
          isLoadingRuns={isLoadingRuns}
          isLoadingRunDetail={isLoadingRunDetail}
          isSendingMessage={isSendingMessage}
          selectedRunId={selectedRunId}
          onDraftChange={setDraft}
          onSendMessage={handleSendMessage}
          onCreateConversation={handleCreateConversation}
          onSelectRun={setSelectedRunId}
        />
      </div>
    </section>
  );
}
