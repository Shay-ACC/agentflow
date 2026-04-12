export default function SettingsPage() {
  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <p className="text-sm uppercase tracking-[0.3em] text-app-muted">
          Settings
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">
          Workspace Settings
        </h1>
        <p className="max-w-2xl text-sm leading-7 text-app-subtle">
          This page will hold workspace-level controls and model or environment
          configuration after the core product flow exists.
        </p>
      </header>

      <div className="rounded-3xl border border-app-border bg-app-panel p-6">
        <p className="text-sm text-app-subtle">
          Placeholder only. No user settings or preferences are implemented.
        </p>
      </div>
    </section>
  );
}
