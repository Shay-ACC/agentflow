"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { dashboardNavigation } from "@/lib/navigation";


type DashboardShellProps = {
  children: React.ReactNode;
};


function DashboardNav() {
  const pathname = usePathname();

  return (
    <nav className="space-y-2">
      {dashboardNavigation.map((item) => {
        const isActive = pathname === item.href;

        return (
          <Link
            key={item.href}
            href={item.href}
            className={[
              "flex items-center justify-between rounded-2xl border px-4 py-3 text-sm transition",
              isActive
                ? "border-app-accent bg-app-panel-soft text-app-text"
                : "border-app-border bg-transparent text-app-subtle hover:border-app-accent hover:text-app-text",
            ].join(" ")}
          >
            <span>{item.label}</span>
            <span className="text-xs text-app-muted">{item.shortLabel}</span>
          </Link>
        );
      })}
    </nav>
  );
}


export function DashboardShell({ children }: DashboardShellProps) {
  return (
    <div className="min-h-screen px-4 py-4 text-app-text sm:px-6 lg:px-8">
      <div className="mx-auto grid min-h-[calc(100vh-2rem)] max-w-7xl gap-4 lg:grid-cols-[260px_minmax(0,1fr)]">
        <aside className="rounded-[28px] border border-app-border bg-app-panel p-5">
          <div className="mb-8 space-y-2">
            <Link href="/" className="inline-flex items-center gap-2">
              <span className="rounded-full bg-app-accent px-2 py-1 text-xs font-semibold uppercase tracking-[0.25em] text-app-accent-foreground">
                AF
              </span>
              <span className="text-sm font-medium text-app-text">AgentFlow</span>
            </Link>
            <p className="text-sm leading-6 text-app-subtle">
              Interview-ready AI agent workspace with a clean, production-style
              shell.
            </p>
          </div>

          <DashboardNav />
        </aside>

        <main className="rounded-[28px] border border-app-border bg-app-panel p-6 sm:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
