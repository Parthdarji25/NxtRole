import type { ReactNode } from "react";

import { RequireSignIn } from "@/features/auth/RequireSignIn";

export default function OnboardingLayout({ children }: { children: ReactNode }) {
  return (
    <RequireSignIn waitingClassName="mx-auto max-w-[880px] px-6 py-10">{children}</RequireSignIn>
  );
}
