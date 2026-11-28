/**
 * Who is signed in, for this browser tab.
 *
 * The 15-minute access token lives only in this module's memory: never in storage, never in
 * a cookie. The 7-day refresh token is a cookie that scripts cannot read; the browser sends
 * it to /api/auth by itself.
 */
import { ApiError, send } from "./http";

export type User = {
  id: string;
  email: string;
  display_name: string | null;
  version: number;
};

export type Session =
  | { status: "unknown" }
  | { status: "signedIn"; user: User }
  /** `chosen` is true when the owner signed out themselves. */
  | { status: "signedOut"; chosen: boolean }
  /** The API did not answer, so it is not known whether the sign-in is still good. */
  | { status: "unreachable" };

type SignedIn = { access_token: string; user: User };

export const CSRF_HEADER = { "X-NxtRole-CSRF": "1" };
const TAB_CHANNEL = "nxtrole-auth";
const TAB_LOCK = "nxtrole-refresh";

const UNKNOWN: Session = { status: "unknown" };

let accessToken: string | null = null;
let session: Session = UNKNOWN;
const listeners = new Set<() => void>();

export function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export const getSession = (): Session => session;
/** While the page is drawn on the server, nobody is known. */
export const getServerSession = (): Session => UNKNOWN;
export const getAccessToken = (): string | null => accessToken;

function change(next: Session): void {
  session = next;
  listeners.forEach((listener) => listener());
}

// --- Telling the other tabs -----------------------------------------------------------

type TabMessage = { type: "signed-in" | "signed-out"; chosen?: boolean };

let channel: BroadcastChannel | null = null;

function tabs(): BroadcastChannel | null {
  if (!channel && typeof BroadcastChannel !== "undefined") {
    channel = new BroadcastChannel(TAB_CHANNEL);
    channel.onmessage = (event: MessageEvent<TabMessage>) => {
      if (event.data.type === "signed-out") {
        forget(event.data.chosen ?? false);
      } else if (session.status === "signedOut") {
        void restore();
      }
    };
  }
  return channel;
}

/** Drops this tab's token and shows it as signed out. */
function forget(chosen: boolean): void {
  accessToken = null;
  change({ status: "signedOut", chosen });
}

/** Signed out here and in every other tab. */
export function endSession(chosen: boolean): void {
  forget(chosen);
  tabs()?.postMessage({ type: "signed-out", chosen } satisfies TabMessage);
}

// --- Refreshing -----------------------------------------------------------------------

/** Lets only one tab refresh at a time, where the browser supports it (D-050). */
function oneTabAtATime<Result>(task: () => Promise<Result>): Promise<Result> {
  if (typeof navigator !== "undefined" && navigator.locks) {
    return navigator.locks.request(TAB_LOCK, task) as Promise<Result>;
  }
  return task();
}

async function askForNewToken(): Promise<boolean> {
  try {
    const answer = await send<{ access_token: string }>("/api/auth/refresh", {
      method: "POST",
      headers: CSRF_HEADER,
    });
    accessToken = answer.access_token;
    return true;
  } catch (error) {
    // Only a refusal means signed out. A network or server problem changes nothing.
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      endSession(false);
      return false;
    }
    throw error;
  }
}

let refreshing: Promise<boolean> | null = null;

/** Gets a new access token. Many callers at the same moment share one request. */
export function refreshAccessToken(): Promise<boolean> {
  refreshing ??= oneTabAtATime(askForNewToken).finally(() => {
    refreshing = null;
  });
  return refreshing;
}

// --- Signing in and out ---------------------------------------------------------------

let restoring: Promise<void> | null = null;

async function loadSession(): Promise<void> {
  tabs();
  try {
    if (!(await refreshAccessToken())) return;
    const user = await send<User>("/api/me", {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    change({ status: "signedIn", user });
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) endSession(false);
    else change({ status: "unreachable" });
  }
}

/** On opening a screen: signs back in with the refresh cookie, if there is one. */
export function restore(): Promise<void> {
  if (session.status === "signedIn") return Promise.resolve();
  if (session.status === "unreachable") change(UNKNOWN);
  restoring ??= loadSession().finally(() => {
    restoring = null;
  });
  return restoring;
}

export async function signIn(email: string, password: string): Promise<User> {
  const answer = await send<SignedIn>("/api/auth/login", {
    method: "POST",
    body: { email, password },
  });
  accessToken = answer.access_token;
  change({ status: "signedIn", user: answer.user });
  tabs()?.postMessage({ type: "signed-in" } satisfies TabMessage);
  return answer.user;
}

/** Signs this device out. If the API cannot be reached, nothing changes and it throws. */
export async function signOut(): Promise<void> {
  try {
    await send("/api/auth/logout", { method: "POST", headers: CSRF_HEADER });
  } catch (error) {
    // A refusal means the sign-in had already ended.
    if (!(error instanceof ApiError && error.status === 401)) throw error;
  }
  endSession(true);
}

/** Keeps the shown name and version current after a change. */
export function updateUser(user: User): void {
  if (session.status === "signedIn") change({ status: "signedIn", user });
}

/** Tests only: back to the state of a newly opened tab. */
export function resetSession(): void {
  accessToken = null;
  session = UNKNOWN;
  refreshing = null;
  restoring = null;
  channel?.close();
  channel = null;
  listeners.clear();
}
