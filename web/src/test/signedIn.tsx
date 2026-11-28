/** Draws a screen as the signed-in owner, against the stand-in API. Test code only. */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render } from "@testing-library/react";
import type { ReactNode } from "react";
import { toast } from "sonner";
import { vi } from "vitest";

import { Toaster } from "@/components/ui/toast";
import { resetSession, signIn } from "@/lib/session";

import { fakeApi, ok, token, USER, type Reply } from "./fakeApi";

export async function renderSignedIn(screen: ReactNode, routes: Record<string, Reply[]>) {
  // The toast library asks about the system's motion setting.
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => ({ matches: true, addEventListener() {}, removeEventListener() {} })),
  );
  const server = fakeApi({
    "POST /api/auth/login": [ok({ access_token: "t", user: USER })],
    "POST /api/auth/refresh": [token("t2")],
    ...routes,
  });
  await signIn("you@example.com", "password");
  const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={queries}>
      {screen}
      <Toaster />
    </QueryClientProvider>,
  );
  return server;
}

/** Call after each test. */
export function signOutAfterTest(): void {
  // Messages live outside the screen, so they would otherwise reach the next test.
  act(() => void toast.dismiss());
  resetSession();
  vi.unstubAllGlobals();
}
