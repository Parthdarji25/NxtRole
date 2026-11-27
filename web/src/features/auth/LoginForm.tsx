"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";

import { loginSchema, type LoginValues } from "./loginSchema";

/**
 * Email and password (D-010). Phase 3 checks the input only; Phase 4 connects it to the API.
 */
export function LoginForm() {
  const [checked, setChecked] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
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
      onSubmit={handleSubmit(
        () => setChecked(true),
        () => setChecked(false),
      )}
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
          <div className="relative">
            <Input
              {...control}
              {...register("password")}
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              className="pr-20"
            />
            <button
              type="button"
              onClick={() => setShowPassword((shown) => !shown)}
              aria-pressed={showPassword}
              aria-label="Show password"
              className="absolute inset-y-0 right-0 min-w-16 rounded-r-[10px] px-3 text-[13px] font-semibold text-ink-2"
            >
              {showPassword ? "Hide" : "Show"}
            </button>
          </div>
        )}
      </Field>
      <Button type="submit" variant="primary" size="lg">
        Sign in
      </Button>
      <p role="status" className="text-sm text-ink-2 empty:hidden">
        {checked ? "Signing in is not ready yet. Nothing was sent." : ""}
      </p>
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
