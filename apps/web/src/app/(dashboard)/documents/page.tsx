export default function DocumentsPage() {
  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <p className="text-sm uppercase tracking-[0.3em] text-app-muted">
          Documents
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">
          Document Library
        </h1>
        <p className="max-w-2xl text-sm leading-7 text-app-subtle">
          This area will later support uploads, indexing status, and document
          management for retrieval workflows.
        </p>
      </header>

      <div className="rounded-3xl border border-app-border bg-app-panel p-6">
        <p className="text-sm text-app-subtle">
          Placeholder only. No upload or retrieval flow has been implemented.
        </p>
      </div>
    </section>
  );
}
