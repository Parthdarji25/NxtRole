"use client";

import { ErrorState } from "@/components/states/states";

export default function RootError({ retry }: { error: unknown; retry: () => void }) {
  return (
    <main className="mx-auto flex min-h-dvh max-w-[720px] flex-col justify-center px-5">
      <ErrorState title="This page did not load" onRetry={retry} />
    </main>
  );
}
