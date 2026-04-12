import type { RunDetail } from "@/lib/api";


type RunDetailPanelProps = {
  run: RunDetail | null;
  isLoading: boolean;
};


function formatDateTime(value: string | null): string {
  if (!value) {
    return "Not finished";
  }

  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}


export function RunDetailPanel({ run, isLoading }: RunDetailPanelProps) {
  return (
    <section className="border-b border-app-border px-6 py-5">
      <div>
        <p className="text-sm uppercase tracking-[0.28em] text-app-muted">
          Run Detail
        </p>
        <p className="mt-2 text-sm leading-7 text-app-subtle">
          Selected trace record for the current conversation.
        </p>
      </div>

      <div className="mt-4">
        {isLoading ? (
          <div className="rounded-2xl border border-dashed border-app-border px-4 py-4 text-sm text-app-subtle">
            Loading run detail...
          </div>
        ) : null}

        {!isLoading && run === null ? (
          <div className="rounded-2xl border border-dashed border-app-border px-4 py-4 text-sm text-app-subtle">
            Select a run in the trace panel to inspect it.
          </div>
        ) : null}

        {!isLoading && run !== null ? (
          <article className="rounded-2xl border border-app-border bg-[#0d1727] px-4 py-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-semibold uppercase tracking-[0.22em] text-app-muted">
                  Run {run.id}
                </span>
                <span
                  className={[
                    "rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.18em]",
                    run.status === "completed"
                      ? "bg-emerald-500/15 text-emerald-300"
                      : run.status === "failed"
                        ? "bg-rose-500/15 text-rose-200"
                        : "bg-amber-500/15 text-amber-200",
                  ].join(" ")}
                >
                  {run.status}
                </span>
              </div>
              <span className="text-xs text-app-muted">
                Conversation {run.conversation_id}
              </span>
            </div>

            <div className="mt-4 grid gap-3 text-sm text-app-subtle sm:grid-cols-2">
              <p>Provider: {run.provider}</p>
              <p>Model: {run.model}</p>
              <p>User message ID: {run.user_message_id}</p>
              <p>Started: {formatDateTime(run.started_at)}</p>
              <p className="sm:col-span-2">Finished: {formatDateTime(run.finished_at)}</p>
            </div>

            <div className="mt-4">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-app-muted">
                User Message
              </p>
              <p className="mt-2 text-sm leading-6 text-app-text">
                {run.user_message_preview}
              </p>
            </div>

            {run.error_message ? (
              <div className="mt-4">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-app-muted">
                  Error
                </p>
                <p className="mt-2 text-sm leading-6 text-rose-200">
                  {run.error_message}
                </p>
              </div>
            ) : null}
          </article>
        ) : null}
      </div>
    </section>
  );
}
