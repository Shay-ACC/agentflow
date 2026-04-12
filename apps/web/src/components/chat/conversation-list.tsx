import type { Conversation } from "@/lib/api";


type ConversationListProps = {
  conversations: Conversation[];
  selectedConversationId: number | null;
  isLoading: boolean;
  isCreating: boolean;
  onCreateConversation: () => void;
  onSelectConversation: (conversationId: number) => void;
};


function formatConversationLabel(conversation: Conversation): string {
  return `Conversation ${conversation.id}`;
}


function formatConversationTime(value: string): string {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}


export function ConversationList({
  conversations,
  selectedConversationId,
  isLoading,
  isCreating,
  onCreateConversation,
  onSelectConversation,
}: ConversationListProps) {
  return (
    <aside className="flex min-h-[620px] flex-col rounded-[28px] border border-app-border bg-app-panel">
      <div className="flex items-center justify-between border-b border-app-border px-5 py-4">
        <div>
          <p className="text-sm uppercase tracking-[0.28em] text-app-muted">
            Conversations
          </p>
          <p className="mt-1 text-sm text-app-subtle">
            Existing chat threads from the backend.
          </p>
        </div>
        <button
          type="button"
          onClick={onCreateConversation}
          disabled={isCreating}
          className="rounded-full bg-app-accent px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-app-accent-foreground transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isCreating ? "Creating" : "New"}
        </button>
      </div>

      <div className="flex-1 space-y-2 overflow-y-auto p-3">
        {isLoading ? (
          <div className="rounded-2xl border border-dashed border-app-border px-4 py-5 text-sm text-app-subtle">
            Loading conversations...
          </div>
        ) : null}

        {!isLoading && conversations.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-app-border px-4 py-5 text-sm text-app-subtle">
            No conversations yet. Create one to start the first thread.
          </div>
        ) : null}

        {!isLoading
          ? conversations.map((conversation) => {
              const isActive = conversation.id === selectedConversationId;

              return (
                <button
                  key={conversation.id}
                  type="button"
                  onClick={() => onSelectConversation(conversation.id)}
                  className={[
                    "w-full rounded-2xl border px-4 py-3 text-left transition",
                    isActive
                      ? "border-app-accent bg-app-panel-soft"
                      : "border-app-border bg-transparent hover:border-app-accent",
                  ].join(" ")}
                >
                  <p className="text-sm font-medium text-app-text">
                    {formatConversationLabel(conversation)}
                  </p>
                  <p className="mt-1 text-xs text-app-muted">
                    {formatConversationTime(conversation.created_at)}
                  </p>
                </button>
              );
            })
          : null}
      </div>
    </aside>
  );
}
