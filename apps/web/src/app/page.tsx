import Link from "next/link";


export default function HomePage() {
  return (
    <main className="min-h-screen bg-app px-6 py-20 text-app-text">
      <div className="mx-auto max-w-5xl">
        <p className="text-sm uppercase tracking-[0.3em] text-app-muted">
          AgentFlow
        </p>
        <h1 className="mt-4 max-w-3xl text-4xl font-semibold tracking-tight sm:text-5xl">
          Portfolio-grade full-stack AI agent system
        </h1>
        <p className="mt-6 max-w-2xl text-lg leading-8 text-app-subtle">
          The frontend foundation is in place with a dashboard shell, feature
          placeholders, and a typed API boundary ready for the first real
          vertical slice.
        </p>
        <div className="mt-10 flex flex-wrap gap-4">
          <Link
            href="/chat"
            className="rounded-full bg-app-accent px-5 py-3 text-sm font-medium text-app-accent-foreground transition hover:opacity-90"
          >
            Open Dashboard
          </Link>
          <Link
            href="/documents"
            className="rounded-full border border-app-border px-5 py-3 text-sm font-medium text-app-text transition hover:border-app-accent hover:text-app-accent"
          >
            Explore Placeholders
          </Link>
        </div>
      </div>
    </main>
  );
}
