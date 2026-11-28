"use client";

import { FormProblem } from "@/components/ui/form-problem";
import { signOut as endThisSignIn } from "@/lib/session";
import { useAction } from "@/lib/useAction";

/** The red "Sign out" line at the foot of the phone's More page (MMore mock). */
export function SignOutButton() {
  const signOut = useAction(endThisSignIn);
  return (
    <div className="flex flex-col items-start gap-2">
      <button
        type="button"
        onClick={() => void signOut.run()}
        aria-busy={signOut.busy || undefined}
        className="inline-flex min-h-11 items-center text-sm font-semibold text-red"
      >
        {signOut.busy ? "Signing out…" : "Sign out"}
      </button>
      <FormProblem>{signOut.problem}</FormProblem>
    </div>
  );
}
