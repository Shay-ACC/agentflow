export default function RunsPage() {
  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <p className="text-sm uppercase tracking-[0.3em] text-app-muted">
          Runs
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">
          Execution Trace
        </h1>
        <p className="max-w-2xl text-sm leading-7 text-app-subtle">
          This page will present task history, tool events, and step-by-step
          execution details once agent workflows exist.
        </p>
      </header>

      <div className="rounded-3xl border border-app-border bg-app-panel p-6">
        <p className="text-sm text-app-subtle">
          Placeholder only. No runs or trace data are connected yet.
        </p>
      </div>
    </section>
  );
}
