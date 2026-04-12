import { RunDetailPanel } from "@/components/chat/run-detail-panel";
import { RunTracePanel } from "@/components/chat/run-trace-panel";
import type { Conversation, Message, Run, RunDetail } from "@/lib/api";


type ChatThreadProps = {
  conversation: Conversation | null;
  messages: Message[];
  runs: Run[];
  selectedRun: RunDetail | null;
  draft: string;
  isLoadingMessages: boolean;
  isLoadingRuns: boolean;
  isLoadingRunDetail: boolean;
  isSendingMessage: boolean;
  selectedRunId: number | null;
  onDraftChange: (value: string) => void;
  onSendMessage: () => void;
  onCreateConversation: () => void;
  onSelectRun: (runId: number) => void;
};


function formatMessageTime(value: string): string {
  return new Intl.DateTimeFormat("en", {
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}


export function ChatThread({
  conversation,
  messages,
  runs,
  selectedRun,
  draft,
  isLoadingMessages,
  isLoadingRuns,
  isLoadingRunDetail,
  isSendingMessage,
  selectedRunId,
  onDraftChange,
  onSendMessage,
  onCreateConversation,
  onSelectRun,
}: ChatThreadProps) {
  const hasConversation = conversation !== null;

  return (
    <section className="flex min-h-[620px] flex-col rounded-[28px] border border-app-border bg-app-panel">
      <header className="border-b border-app-border px-6 py-5">
        <p className="text-sm uppercase tracking-[0.28em] text-app-muted">
          Chat
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-app-text">
          {hasConversation ? `Conversation ${conversation.id}` : "Agent Chat"}
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-7 text-app-subtle">
          Minimal end-to-end frontend integration against the existing
          conversation and message backend endpoints.
        </p>
      </header>

      {!hasConversation ? (
        <div className="flex flex-1 flex-col items-center justify-center px-6 text-center">
          <div className="max-w-md rounded-3xl border border-dashed border-app-border px-8 py-10">
            <h2 className="text-xl font-semibold text-app-text">
              Start the first conversation
            </h2>
            <p className="mt-3 text-sm leading-7 text-app-subtle">
              Create a conversation on the left or use the button below to open
              a new thread and send the first message.
            </p>
            <button
              type="button"
              onClick={onCreateConversation}
              className="mt-6 rounded-full bg-app-accent px-5 py-3 text-sm font-semibold text-app-accent-foreground transition hover:opacity-90"
            >
              New Conversation
            </button>
          </div>
        </div>
      ) : (
        <>
          <RunTracePanel
            runs={runs}
            isLoadingRuns={isLoadingRuns}
            selectedRunId={selectedRunId}
            onSelectRun={onSelectRun}
          />
          <RunDetailPanel run={selectedRun} isLoading={isLoadingRunDetail} />

          <div className="flex-1 space-y-4 overflow-y-auto px-6 py-5">
            {isLoadingMessages ? (
              <div className="rounded-2xl border border-dashed border-app-border px-4 py-5 text-sm text-app-subtle">
                Loading messages...
              </div>
            ) : null}

            {!isLoadingMessages && messages.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-app-border px-4 py-5 text-sm text-app-subtle">
                No messages yet. Send the first user message below.
              </div>
            ) : null}

            {!isLoadingMessages
              ? messages.map((message) => {
                  const isUser = message.role === "user";

                  return (
                    <article
                      key={message.id}
                      className={[
                        "max-w-3xl rounded-3xl border px-5 py-4",
                        isUser
                          ? "ml-auto border-app-accent bg-app-panel-soft"
                          : "border-app-border bg-[#0d1727]",
                      ].join(" ")}
                    >
                      <div className="flex items-center justify-between gap-4">
                        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-app-muted">
                          {message.role}
                        </p>
                        <p className="text-xs text-app-muted">
                          {formatMessageTime(message.created_at)}
                        </p>
                      </div>
                      <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-app-text">
                        {message.content}
                      </p>
                    </article>
                  );
                })
              : null}
          </div>

          <form
            className="border-t border-app-border px-6 py-5"
            onSubmit={(event) => {
              event.preventDefault();
              onSendMessage();
            }}
          >
            <label className="block">
              <span className="sr-only">Message</span>
              <textarea
                value={draft}
                onChange={(event) => onDraftChange(event.target.value)}
                placeholder="Send a message to the selected conversation..."
                rows={4}
                className="w-full resize-none rounded-3xl border border-app-border bg-[#0b1422] px-4 py-4 text-sm text-app-text outline-none transition placeholder:text-app-muted focus:border-app-accent"
              />
            </label>
            <div className="mt-4 flex items-center justify-between gap-4">
              <p className="text-xs text-app-muted">
                Messages are stored through the existing backend endpoints only.
              </p>
              <button
                type="submit"
                disabled={isSendingMessage || draft.trim().length === 0}
                className="rounded-full bg-app-accent px-5 py-3 text-sm font-semibold text-app-accent-foreground transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSendingMessage ? "Sending..." : "Send Message"}
              </button>
            </div>
          </form>
        </>
      )}
    </section>
  );
}
