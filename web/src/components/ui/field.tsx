"use client";

import { Label as LabelPrimitive } from "radix-ui";
import { useId, type ComponentProps, type ReactNode } from "react";

import { cn } from "@/lib/cn";

const CONTROL =
  "w-full border border-rule-2 bg-card text-ink text-[15px] placeholder:text-ink-3 " +
  "disabled:cursor-not-allowed disabled:opacity-50 aria-invalid:border-red";

export function Label({ className, ...props }: ComponentProps<typeof LabelPrimitive.Root>) {
  return <LabelPrimitive.Root className={cn("text-[13px] font-semibold", className)} {...props} />;
}

export function Input({ className, ...props }: ComponentProps<"input">) {
  return <input className={cn(CONTROL, "h-12 rounded-[10px] px-3.5", className)} {...props} />;
}

export function Textarea({ className, ...props }: ComponentProps<"textarea">) {
  return (
    <textarea className={cn(CONTROL, "min-h-28 rounded-[10px] p-3.5", className)} {...props} />
  );
}

/** The browser's own select: familiar, accessible and good on phones. */
export function Select({ className, ...props }: ComponentProps<"select">) {
  return (
    <select
      className={cn(CONTROL, "h-11 w-auto rounded-[var(--radius-input)] px-2 text-sm", className)}
      {...props}
    />
  );
}

export type FieldControlProps = {
  id: string;
  "aria-invalid": true | undefined;
  "aria-describedby": string | undefined;
};

/** A visible label, an optional hint and the error message, all tied to the control. */
export function Field({
  label,
  hint,
  error,
  className,
  children,
}: {
  label: string;
  hint?: string;
  error?: string;
  className?: string;
  children: (control: FieldControlProps) => ReactNode;
}) {
  const id = useId();
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;

  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <Label htmlFor={id}>{label}</Label>
      {children({
        id,
        "aria-invalid": error ? true : undefined,
        "aria-describedby": [errorId, hintId].filter(Boolean).join(" ") || undefined,
      })}
      {hint && (
        <span id={hintId} className="text-[13px] text-ink-3">
          {hint}
        </span>
      )}
      {error && (
        <span id={errorId} role="alert" className="text-[13px] text-red">
          {error}
        </span>
      )}
    </div>
  );
}
