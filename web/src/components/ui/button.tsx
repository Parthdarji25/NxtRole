import { Slot } from "radix-ui";
import type { ComponentProps } from "react";

import { cn } from "@/lib/cn";

export type ButtonVariant = "primary" | "ink" | "outline" | "text";
export type ButtonSize = "md" | "sm" | "lg";

const BASE =
  "inline-flex items-center justify-center gap-2 font-semibold whitespace-nowrap no-underline " +
  "transition-colors duration-250 disabled:cursor-not-allowed disabled:opacity-50 " +
  "aria-disabled:cursor-not-allowed aria-disabled:opacity-50";

// Values from the mocks (Foundations, Jobs, Login).
const VARIANTS: Record<ButtonVariant, string> = {
  // The one blue action of a screen.
  primary: "bg-blue text-on-blue hover:text-on-blue hover:brightness-110 border border-blue",
  ink: "bg-ink text-paper hover:text-paper border border-ink hover:opacity-90",
  outline: "border border-rule-2 bg-transparent text-ink hover:bg-card hover:text-ink",
  text: "border border-transparent bg-transparent text-ink-3 font-normal hover:text-ink hover:underline",
};

const SIZES: Record<ButtonSize, string> = {
  lg: "min-h-[50px] rounded-[10px] px-5 text-[15px]",
  md: "min-h-11 rounded-[var(--radius-button)] px-4 text-sm",
  // Looks 34px high but has a 44px touch area.
  sm: "hit-target min-h-[34px] rounded-[7px] px-3 text-[13px]",
};

export type ButtonProps = ComponentProps<"button"> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  /** Shows a spinner, keeps the width and blocks further clicks. */
  loading?: boolean;
  /** Renders the child element (for example a link) with the button's look. */
  asChild?: boolean;
};

export function Button({
  variant = "outline",
  size = "md",
  loading = false,
  asChild = false,
  className,
  children,
  disabled,
  type,
  ...props
}: ButtonProps) {
  const classes = cn(BASE, VARIANTS[variant], SIZES[size], loading && "relative", className);

  if (asChild) {
    return (
      <Slot.Root className={classes} data-variant={variant} {...props}>
        {children}
      </Slot.Root>
    );
  }

  return (
    <button
      type={type ?? "button"}
      className={classes}
      data-variant={variant}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading && (
        <span
          aria-hidden="true"
          className="absolute size-4 animate-spin rounded-full border-2 border-current border-t-transparent"
        />
      )}
      <span className={cn("inline-flex items-center gap-2", loading && "opacity-0")}>
        {children}
      </span>
    </button>
  );
}
