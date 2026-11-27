"use client";

import { Switch as SwitchPrimitive } from "radix-ui";
import type { ComponentProps } from "react";

import { cn } from "@/lib/cn";

/** 44 × 24 toggle from the Foundations board. Always give it a label (`aria-label` or <Label>). */
export function Switch({ className, ...props }: ComponentProps<typeof SwitchPrimitive.Root>) {
  return (
    <SwitchPrimitive.Root
      className={cn(
        "hit-target inline-flex h-6 w-11 shrink-0 items-center rounded-full border-[1.5px] p-0.5",
        "border-ink-3 bg-transparent transition-colors duration-250",
        "data-[state=checked]:border-ink data-[state=checked]:bg-ink",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    >
      <SwitchPrimitive.Thumb
        className={cn(
          "block size-4 rounded-full bg-ink-3 transition-transform duration-250",
          "data-[state=checked]:translate-x-[21px] data-[state=checked]:bg-paper",
        )}
      />
    </SwitchPrimitive.Root>
  );
}
