"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { ErrorState, PageSkeleton } from "@/components/states/states";
import { UNREACHABLE } from "@/lib/http";
import { loginHref } from "@/lib/safeNext";
import { restore } from "@/lib/session";
import { useSession } from "@/lib/useSession";

/**
 * Shows its screens only to the signed-in owner.
 *
 * This is for convenience: the real lock is the API, which refuses every request without a
 * valid sign-in.
 */
export function RequireSignIn({
  children,
  waitingClassName,
}: {
  children: ReactNode;
  /** Spacing for the placeholders on a screen without the app frame. */
  waitingClassName?: string;
}) {
  const session = useSession();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (session.status === "unknown") void restore();
    if (session.status === "signedOut") {
      // After choosing to sign out there is no screen to return to.
      const here = pathname + window.location.search;
      router.replace(session.chosen ? "/login" : loginHref(here));
    }
    // Only a change of the sign-in state matters here.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session.status]);

  if (session.status !== "signedIn") {
    return (
      <div className={waitingClassName}>
        {session.status === "unreachable" ? (
          <ErrorState onRetry={() => void restore()}>{UNREACHABLE}</ErrorState>
        ) : (
          <PageSkeleton />
        )}
      </div>
    );
  }
  return <ServerData key={session.user.id}>{children}</ServerData>;
}

/** The cache of server data. It lives only while this user is signed in. */
function ServerData({ children }: { children: ReactNode }) {
  const [queries] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          // The API client already refreshes expired tokens; one more try covers a blip.
          queries: { retry: 1, refetchOnWindowFocus: false },
        },
      }),
  );
  return <QueryClientProvider client={queries}>{children}</QueryClientProvider>;
}
