"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchReadiness, type Readiness } from "./fetchReadiness";

export function HealthCheck() {
  // null means "still checking".
  const [result, setResult] = useState<Readiness | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    void fetchReadiness(controller.signal).then((readiness) => {
      if (!controller.signal.aborted) setResult(readiness);
    });
    return () => controller.abort();
  }, [attempt]);

  const retry = useCallback(() => {
    setResult(null);
    setAttempt((count) => count + 1);
  }, []);

  const healthy = result?.kind === "checked" && result.database === "ok" && result.redis === "ok";

  return (
    <section aria-label="Service health" className="rounded-xl border border-rule bg-card p-4">
      <p role="status" className="font-mono text-sm">
        {result === null && "Checking services…"}
        {result?.kind === "checked" && `database ${result.database}, redis ${result.redis}`}
        {result?.kind === "unreachable" && "The API cannot be reached."}
      </p>
      {result !== null && !healthy && (
        <>
          <p className="mt-2 text-sm text-ink-2">
            Check that the containers and the API are running (see the README), then try again.
          </p>
          <button
            type="button"
            onClick={retry}
            className="mt-3 min-h-11 cursor-pointer rounded-lg border border-rule-2 px-4 text-sm font-semibold"
          >
            Retry
          </button>
        </>
      )}
    </section>
  );
}
