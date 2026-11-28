/**
 * One way of calling the API: JSON in, JSON out, and every problem as an `ApiError`
 * with a message a person can read.
 */

export type ApiProblem = {
  code: string;
  message: string;
  retry_after_seconds?: number;
  fields?: { field: string; message: string }[];
};

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly retryAfterSeconds?: number;

  constructor(status: number, problem: ApiProblem) {
    super(problem.message);
    this.name = "ApiError";
    this.status = status;
    this.code = problem.code;
    this.retryAfterSeconds = problem.retry_after_seconds;
  }
}

export const UNREACHABLE = "NxtRole cannot be reached. Check your connection and try again.";

/** A call that gets no answer is given up after this long. */
export const TIMEOUT_MILLISECONDS = 15_000;
/** Sending a file, or having it read, may take longer on a slow connection. */
export const SLOW_TIMEOUT_MILLISECONDS = 60_000;

export type SendOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  /** Sent as JSON; a file is sent as it is. */
  body?: unknown;
  headers?: Record<string, string>;
  timeout?: number;
};

function isProblem(value: unknown): value is { detail: ApiProblem } {
  const detail = (value as { detail?: Partial<ApiProblem> } | null)?.detail;
  return typeof detail?.code === "string" && typeof detail.message === "string";
}

/** Sends one request. Returns the answer's body, or `undefined` when there is none. */
export async function send<Result>(path: string, options: SendOptions = {}): Promise<Result> {
  const { method = "GET", body, headers = {}, timeout = TIMEOUT_MILLISECONDS } = options;
  const isFile = body instanceof Blob;
  const json = body !== undefined && !isFile;
  let response: Response;
  try {
    response = await fetch(path, {
      method,
      headers: json ? { "Content-Type": "application/json", ...headers } : headers,
      body: isFile ? body : json ? JSON.stringify(body) : undefined,
      // The refresh cookie belongs to this site only.
      credentials: "same-origin",
      cache: "no-store",
      signal: AbortSignal.timeout(timeout),
    });
  } catch {
    throw new ApiError(0, { code: "unreachable", message: UNREACHABLE });
  }

  if (response.status === 204) return undefined as Result;
  const answer: unknown = await response.json().catch(() => null);
  if (response.ok && answer !== null) return answer as Result;
  // An answer that is not ours (for example from the forwarding server when the API is
  // stopped) is treated as "cannot be reached".
  throw new ApiError(
    response.status,
    isProblem(answer) ? answer.detail : { code: "unreachable", message: UNREACHABLE },
  );
}
