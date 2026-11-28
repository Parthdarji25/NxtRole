"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { FormProblem } from "@/components/ui/form-problem";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { PasswordInput } from "@/features/auth/PasswordInput";
import { newPassword, NOT_THE_SAME } from "@/features/auth/passwordRules";
import { useAction } from "@/lib/useAction";

const passwordSchema = z
  .object({
    current_password: z.string().min(1, "Enter your current password."),
    new_password: newPassword,
    again: z.string(),
  })
  .refine((values) => values.new_password === values.again, {
    path: ["again"],
    message: NOT_THE_SAME,
  });

type FormValues = z.infer<typeof passwordSchema>;
export type PasswordValues = Omit<FormValues, "again">;

function PasswordForm({
  onChange,
  onDone,
}: {
  onChange: (values: PasswordValues) => Promise<unknown>;
  onDone: () => void;
}) {
  const change = useAction(onChange);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: { current_password: "", new_password: "", again: "" },
  });

  return (
    <form
      noValidate
      method="post"
      onSubmit={handleSubmit(async ({ current_password, new_password }) => {
        if (await change.run({ current_password, new_password })) onDone();
      }, change.clear)}
      className="flex flex-col gap-5"
    >
      <Field label="Current password" error={errors.current_password?.message}>
        {(control) => (
          <PasswordInput
            {...control}
            {...register("current_password")}
            showLabel="Show current password"
            autoComplete="current-password"
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
      <FormProblem>{change.problem}</FormProblem>
      <Button type="submit" variant="primary" size="lg" loading={change.busy}>
        Change password
      </Button>
    </form>
  );
}

/** "Change password": a drawer, as the mocks use for details. */
export function ChangePassword({
  onChange,
}: {
  onChange: (values: PasswordValues) => Promise<unknown>;
}) {
  const [open, setOpen] = useState(false);
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button size="sm">Change password</Button>
      </SheetTrigger>
      <SheetContent title="Change password" description="Your other devices will be signed out.">
        <PasswordForm onChange={onChange} onDone={() => setOpen(false)} />
      </SheetContent>
    </Sheet>
  );
}
