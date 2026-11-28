/** Calls to the API as the signed-in owner. */
import { ApiError, send, type SendOptions } from "./http";
import { endSession, getAccessToken, refreshAccessToken } from "./session";

export { ApiError } from "./http";

function signedOut(): ApiError {
  return new ApiError(401, { code: "unauthorized", message: "Sign in to continue." });
}

function withToken<Result>(path: string, options: SendOptions): Promise<Result> {
  return send<Result>(path, {
    ...options,
    headers: { ...options.headers, Authorization: `Bearer ${getAccessToken()}` },
  });
}

/**
 * Adds the access token. When it has run out, gets a new one (once, however many requests
 * are waiting) and tries the request one more time (E-56).
 */
export async function api<Result>(path: string, options: SendOptions = {}): Promise<Result> {
  if (!getAccessToken() && !(await refreshAccessToken())) throw signedOut();
  const used = getAccessToken();
  try {
    return await withToken<Result>(path, options);
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 401) throw error;
    if (error.code === "token_expired") {
      // Another request may already have fetched a newer token.
      if (getAccessToken() === used && !(await refreshAccessToken())) throw error;
      return withToken<Result>(path, options);
    }
    // "unauthorized" means this sign-in has ended; other 401s are about the request itself.
    if (error.code === "unauthorized") endSession(false);
    throw error;
  }
}
