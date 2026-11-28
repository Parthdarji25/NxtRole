/** A stand-in for the API in component tests. Test code only. */
import { vi } from "vitest";

export type Reply = { status: number; body?: unknown } | "offline";

export const problem = (status: number, code: string, message = code): Reply => ({
  status,
  body: { detail: { code, message } },
});

export const USER = { id: "u1", email: "you@example.com", display_name: null, version: 1 };

/**
 * Answers each "METHOD /path" with the next reply in its list; the last one repeats.
 * Returns the calls made, in order.
 */
export function fakeApi(routes: Record<string, Reply[]>) {
  const calls: { route: string; headers: Record<string, string>; body: unknown }[] = [];
  const used = new Map<string, number>();
  vi.stubGlobal(
    "fetch",
    vi.fn(async (path: string, init: RequestInit) => {
      const route = `${init.method} ${path}`;
      calls.push({
        route,
        headers: (init.headers ?? {}) as Record<string, string>,
        body: init.body ? JSON.parse(init.body as string) : undefined,
      });
      const replies = routes[route];
      if (!replies) throw new Error(`unexpected request: ${route}`);
      const index = used.get(route) ?? 0;
      used.set(route, index + 1);
      const reply = replies[Math.min(index, replies.length - 1)]!;
      // Answers take a moment, so that requests can overlap as they do for real.
      await new Promise((resolve) => setTimeout(resolve, 5));
      if (reply === "offline") throw new TypeError("network down");
      return new Response(reply.status === 204 ? null : JSON.stringify(reply.body ?? null), {
        status: reply.status,
      });
    }),
  );
  return {
    calls,
    count: (route: string) => calls.filter((call) => call.route === route).length,
  };
}

export const token = (value: string): Reply => ({ status: 200, body: { access_token: value } });
export const ok = (body: unknown): Reply => ({ status: 200, body });
