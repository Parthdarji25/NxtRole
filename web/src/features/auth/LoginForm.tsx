"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";
import { FormProblem } from "@/components/ui/form-problem";
import { useAction } from "@/lib/useAction";

import { loginSchema, type LoginValues } from "./loginSchema";
import { PasswordInput } from "./PasswordInput";

/** Email and password (D-010). The API decides whether they are right. */
export function LoginForm({
  onSignIn,
}: {
  /** Signs in, or throws with the reason. */
  onSignIn: (values: LoginValues) => Promise<unknown>;
}) {
  const signIn = useAction(onSignIn);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  return (
    <form
      noValidate
      // If this form were ever sent before the script loaded, the password must not
      // end up in the address bar.
      method="post"
      onSubmit={handleSubmit((values) => signIn.run(values), signIn.clear)}
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
      <Field label="Password" error={errors.password?.message}>
        {(control) => (
          <PasswordInput {...control} {...register("password")} autoComplete="current-password" />
        )}
      </Field>
      <FormProblem>{signIn.problem}</FormProblem>
      <Button type="submit" variant="primary" size="lg" loading={signIn.busy}>
        Sign in
      </Button>
      <p className="border-t border-rule pt-4 text-xs text-ink-3">
        By continuing you agree to the{" "}
        <Link href="/terms" className="underline">
          Terms
        </Link>{" "}
        and{" "}
        <Link href="/privacy" className="underline">
          Privacy notice
        </Link>
        . NxtRole never posts or applies anywhere without your approval.
      </p>
    </form>
  );
}
