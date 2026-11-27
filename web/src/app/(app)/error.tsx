"use client";

import { ErrorState } from "@/components/states/states";

// The error's own text is not shown: it could contain technical or personal details.
export default function AppError({ retry }: { error: unknown; retry: () => void }) {
  return <ErrorState title="This screen did not load" onRetry={retry} />;
}
