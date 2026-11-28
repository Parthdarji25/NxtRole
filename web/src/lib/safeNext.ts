export const HOME = "/today";

/**
 * The screen to open after signing in. The value comes from the address bar, so only a path
 * inside this site is accepted; anything else could send the owner to a look-alike website.
 */
export function safeNext(value: string | string[] | undefined): string {
  if (typeof value !== "string" || value.length > 500) return HOME;
  // Must start with one slash; browsers treat "//host" and "/\host" as another site.
  if (!/^\/(?![/\\])[^\\\u0000-\u001f]*$/.test(value)) return HOME;
  if (value === "/login" || value.startsWith("/login?") || value.startsWith("/login/")) {
    return HOME;
  }
  return value;
}

/** The sign-in address that comes back to `path` afterwards (FR-006). */
export function loginHref(path: string): string {
  return path === HOME ? "/login" : `/login?next=${encodeURIComponent(path)}`;
}
