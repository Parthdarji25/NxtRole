"use client";

import { send } from "@/lib/http";
import { endSession } from "@/lib/session";

import { AuthLayout } from "./AuthLayout";
import { RecoverForm, type RecoverValues } from "./RecoverForm";

async function recover(values: Omit<RecoverValues, "again">): Promise<string> {
  const answer = await send<{ recovery_code: string }>("/api/auth/recover", {
    method: "POST",
    body: values,
  });
  // The API has signed every device out; open tabs should say so too.
  endSession(false);
  return answer.recovery_code;
}

export function RecoverScreen() {
  return (
    <AuthLayout
      title="Get back in"
      phoneTitle="Get back in."
      phoneLead="Use your recovery code to set a new password."
    >
      <RecoverForm onRecover={recover} />
    </AuthLayout>
  );
}
