"use client";

import { DropdownMenu as MenuPrimitive, Tooltip as TooltipPrimitive } from "radix-ui";
import type { ComponentProps, ReactNode } from "react";

import { cn } from "@/lib/cn";

export const DropdownMenu = MenuPrimitive.Root;
export const DropdownMenuTrigger = MenuPrimitive.Trigger;

export function DropdownMenuContent({
  className,
  ...props
}: ComponentProps<typeof MenuPrimitive.Content>) {
  return (
    <MenuPrimitive.Portal>
      <MenuPrimitive.Content
        sideOffset={6}
        className={cn(
          "z-50 min-w-48 animate-fade-in rounded-[var(--radius-panel)] border border-rule bg-card p-1 text-ink shadow-overlay",
          className,
        )}
        {...props}
      />
    </MenuPrimitive.Portal>
  );
}

export function DropdownMenuItem({
  className,
  ...props
}: ComponentProps<typeof MenuPrimitive.Item>) {
  return (
    <MenuPrimitive.Item
      className={cn(
        "flex min-h-11 cursor-pointer items-center gap-2 rounded-lg px-3 text-sm outline-none",
        "data-highlighted:bg-blue-soft data-highlighted:text-blue-ink",
        className,
      )}
      {...props}
    />
  );
}

/** A short hint on hover or keyboard focus. Never the only place for important information. */
export function Tooltip({ text, children }: { text: string; children: ReactNode }) {
  return (
    <TooltipPrimitive.Provider delayDuration={300}>
      <TooltipPrimitive.Root>
        <TooltipPrimitive.Trigger asChild>{children}</TooltipPrimitive.Trigger>
        <TooltipPrimitive.Portal>
          <TooltipPrimitive.Content
            sideOffset={6}
            className="z-50 max-w-60 animate-fade-in rounded-md bg-ink px-2.5 py-1.5 text-xs text-paper"
          >
            {text}
          </TooltipPrimitive.Content>
        </TooltipPrimitive.Portal>
      </TooltipPrimitive.Root>
    </TooltipPrimitive.Provider>
  );
}
