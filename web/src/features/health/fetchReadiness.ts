export type CheckResult = "ok" | "error";

export type Readiness =
  { kind: "checked"; database: CheckResult; redis: CheckResult } | { kind: "unreachable" };

const TIMEOUT_MS = 10_000;

function isCheckResult(value: unknown): value is CheckResult {
  return value === "ok" || value === "error";
}

function readChecks(body: unknown): Readiness | null {
  if (typeof body !== "object" || body === null) return null;
  // A healthy answer holds the checks at the top; a 503 holds them under detail.checks.
  const detail = (body as { detail?: { checks?: unknown } }).detail;
  const checks = (detail?.checks ?? body) as { database?: unknown; redis?: unknown };
  if (!isCheckResult(checks.database) || !isCheckResult(checks.redis)) return null;
  return { kind: "checked", database: checks.database, redis: checks.redis };
}

/** Asks the API (through the /api forwarding) whether its services answer. Never throws. */
export async function fetchReadiness(signal?: AbortSignal): Promise<Readiness> {
  const timeout = AbortSignal.timeout(TIMEOUT_MS);
  try {
    const response = await fetch("/api/health/ready", {
      cache: "no-store",
      signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
    });
    return readChecks(await response.json()) ?? { kind: "unreachable" };
  } catch {
    // No network, the API is not running, or the answer was not JSON.
    return { kind: "unreachable" };
  }
}
