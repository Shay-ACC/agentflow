import type { Run } from "@/lib/api";


type RunTracePanelProps = {
  runs: Run[];
  isLoadingRuns: boolean;
  selectedRunId: number | null;
  onSelectRun: (runId: number) => void;
};


function formatRunTime(value: string | null): string {
  if (!value) {
    return "In progress";
  }

  return new Intl.DateTimeFormat("en", {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}


export function RunTracePanel({
  runs,
  isLoadingRuns,
  selectedRunId,
  onSelectRun,
}: RunTracePanelProps) {
  return (
    <section className="border-b border-app-border px-6 py-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.28em] text-app-muted">
            Trace
          </p>
          <p className="mt-2 text-sm leading-7 text-app-subtle">
            Run record for each user message send.
          </p>
        </div>
      </div>

      <div className="mt-4 space-y-3">
        {isLoadingRuns ? (
          <div className="rounded-2xl border border-dashed border-app-border px-4 py-4 text-sm text-app-subtle">
            Loading runs...
          </div>
        ) : null}

        {!isLoadingRuns && runs.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-app-border px-4 py-4 text-sm text-app-subtle">
            No runs recorded yet for this conversation.
          </div>
        ) : null}

        {!isLoadingRuns
          ? runs.map((run) => (
              <button
                key={run.id}
                type="button"
                onClick={() => onSelectRun(run.id)}
                className="rounded-2xl border border-app-border bg-[#0d1727] px-4 py-4"
              >
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
                  <p className="text-xs text-app-muted">
                    {formatRunTime(run.started_at)}
                    {" -> "}
                    {formatRunTime(run.finished_at)}
                  </p>
                </div>

                <div className="mt-3 flex flex-wrap gap-4 text-xs text-app-subtle">
                  <span>Provider: {run.provider}</span>
                  <span>Model: {run.model}</span>
                  <span>User message: {run.user_message_id}</span>
                  {selectedRunId === run.id ? <span>Selected</span> : null}
                </div>

                <p className="mt-3 text-sm leading-6 text-app-text">
                  {run.user_message_preview}
                </p>

                {run.error_message ? (
                  <p className="mt-3 text-xs leading-6 text-rose-200">
                    {run.error_message}
                  </p>
                ) : null}
              </button>
            ))
          : null}
      </div>
    </section>
  );
}
