"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";
import { FormProblem } from "@/components/ui/form-problem";
import { useAction } from "@/lib/useAction";

import { loginSchema } from "./loginSchema";
import { PasswordInput } from "./PasswordInput";
import { newPassword, NOT_THE_SAME } from "./passwordRules";
import { RecoveryCode } from "./RecoveryCode";

export const recoverSchema = z
  .object({
    email: loginSchema.shape.email,
    recovery_code: z
      .string()
      .trim()
      .min(1, "Enter your recovery code.")
      .max(80, "That code is too long."),
    new_password: newPassword,
    again: z.string(),
  })
  .refine((values) => values.new_password === values.again, {
    path: ["again"],
    message: NOT_THE_SAME,
  });

export type RecoverValues = z.infer<typeof recoverSchema>;

/** A new password with the recovery code; then the next code, shown once (D-027). */
export function RecoverForm({
  onRecover,
}: {
  /** Returns the new recovery code, or throws with the reason. */
  onRecover: (values: Omit<RecoverValues, "again">) => Promise<string>;
}) {
  const [nextCode, setNextCode] = useState<string | null>(null);
  const recover = useAction(async ({ email, recovery_code, new_password }: RecoverValues) => {
    setNextCode(await onRecover({ email, recovery_code, new_password }));
  });
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RecoverValues>({
    resolver: zodResolver(recoverSchema),
    defaultValues: { email: "", recovery_code: "", new_password: "", again: "" },
  });

  if (nextCode) {
    return (
      <div className="flex flex-col gap-[22px]">
        <p role="status" className="text-ink-2">
          Your password is changed, and every device has been signed out.
        </p>
        <RecoveryCode code={nextCode} />
        <Button asChild variant="primary" size="lg">
          <Link href="/login">I have saved it: sign in</Link>
        </Button>
      </div>
    );
  }

  return (
    <form
      noValidate
      method="post"
      onSubmit={handleSubmit((values) => recover.run(values), recover.clear)}
      className="flex flex-col gap-[22px]"
    >
      <Field label="Email" error={errors.email?.message}>
        {(control) => (
          <Input
            {...control}
            {...register("email")}
            type="email"
            autoComplete="username"
            inputMode="email"
            placeholder="you@example.com"
          />
        )}
      </Field>
      <Field
        label="Recovery code"
        hint="The code you saved when the account was created. Dashes and capitals do not matter."
        error={errors.recovery_code?.message}
      >
        {(control) => (
          <Input
            {...control}
            {...register("recovery_code")}
            autoComplete="off"
            autoCapitalize="characters"
            spellCheck={false}
            className="font-mono"
          />
        )}
      </Field>
      <Field
        label="New password"
        hint="At least 12 characters."
        error={errors.new_password?.message}
      >
        {(control) => (
          <PasswordInput
            {...control}
            {...register("new_password")}
            showLabel="Show new password"
            autoComplete="new-password"
          />
        )}
      </Field>
      <Field label="New password again" error={errors.again?.message}>
        {(control) => (
          <PasswordInput
            {...control}
            {...register("again")}
            showLabel="Show repeated password"
            autoComplete="new-password"
          />
        )}
      </Field>
      <FormProblem>{recover.problem}</FormProblem>
      <Button type="submit" variant="primary" size="lg" loading={recover.busy}>
        Set new password
      </Button>
      <p className="border-t border-rule pt-4 text-sm text-ink-3">
        Lost the code too? On your own computer, run the <code>reset-password</code> command
        described in the README.{" "}
        <Link href="/login" className="underline">
          Back to sign in
        </Link>
      </p>
    </form>
  );
}
