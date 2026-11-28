"use client";

import type { ComponentProps } from "react";

import { cn } from "@/lib/cn";

/** A choice that can be switched on and off, such as a job title or a city. */
export function Chip({
  pressed,
  onPressedChange,
  look = "soft",
  className,
  children,
  ...props
}: Omit<ComponentProps<"button">, "aria-pressed"> & {
  pressed: boolean;
  onPressedChange: (pressed: boolean) => void;
  /** "ink" is the filled chip of the setup steps: squarer on desktop, ticked on phones. */
  look?: "soft" | "ink";
}) {
  const ink = look === "ink";
  return (
    <button
      type="button"
      aria-pressed={pressed}
      onClick={() => onPressedChange(!pressed)}
      className={cn(
        "inline-flex min-h-11 items-center gap-2 rounded-full border px-4 text-sm font-medium",
        "transition-colors duration-250",
        ink && "text-[15px] font-semibold md:rounded-lg md:text-sm md:font-medium",
        pressed
          ? ink
            ? "border-ink bg-ink text-paper"
            : "border-blue bg-blue-soft text-blue-ink"
          : "border-rule-2 bg-transparent text-ink-2",
        className,
      )}
      {...props}
    >
      {pressed && (
        <span aria-hidden="true" className={cn(ink && "md:hidden")}>
          ✓
        </span>
      )}
      {children}
    </button>
  );
}
