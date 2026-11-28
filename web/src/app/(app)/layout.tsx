import type { ReactNode } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { RequireSignIn } from "@/features/auth/RequireSignIn";

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <AppShell>
      <RequireSignIn waitingClassName="flex flex-col gap-7">{children}</RequireSignIn>
    </AppShell>
  );
}
