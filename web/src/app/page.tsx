import { HealthCheck } from "@/features/health/HealthCheck";

// Temporary developer check, not a product screen. Phase 3 replaces this page.
export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col justify-center gap-4 px-4">
      <p className="font-mono text-xs tracking-widest text-ink-3 uppercase">Developer check</p>
      <h1 className="text-3xl font-semibold tracking-tight">
        Nxt<span className="text-blue">Role</span>
      </h1>
      <p className="text-ink-2">
        This page asks the API whether the database and Redis answer. It will be replaced by the
        real screens in Phase 3.
      </p>
      <HealthCheck />
    </main>
  );
}
