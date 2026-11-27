"use client";

import { Dialog as DialogPrimitive } from "radix-ui";
import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

import { Icon } from "./icons";

/**
 * A drawer from the right ("Add a job", "Agent log"). Radix traps the keyboard focus inside,
 * closes it with Escape and gives the focus back to the button that opened it.
 */
export const Sheet = DialogPrimitive.Root;
export const SheetTrigger = DialogPrimitive.Trigger;
export const SheetClose = DialogPrimitive.Close;

export function SheetContent({
  title,
  kicker,
  description,
  className,
  children,
}: {
  title: string;
  kicker?: string;
  description?: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="fixed inset-0 z-40 animate-fade-in bg-scrim" />
      <DialogPrimitive.Content
        // Without a description, tell Radix on purpose instead of leaving a broken reference.
        {...(description ? {} : { "aria-describedby": undefined })}
        className={cn(
          "fixed inset-y-0 right-0 z-41 flex w-[min(460px,100vw)] flex-col gap-5 overflow-y-auto",
          "animate-slide-in border-l border-rule bg-paper p-7 text-ink shadow-overlay",
          className,
        )}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 flex-col gap-1">
            {kicker && <span className="kicker tracking-[0.08em]">{kicker}</span>}
            <DialogPrimitive.Title className="heading text-[32px]">{title}</DialogPrimitive.Title>
            {description && (
              <DialogPrimitive.Description className="text-[13px] text-ink-3">
                {description}
              </DialogPrimitive.Description>
            )}
          </div>
          <DialogPrimitive.Close
            aria-label="Close"
            className="hit-target inline-flex size-9 shrink-0 items-center justify-center rounded-lg border border-rule text-ink-2"
          >
            <Icon name="close" size={16} />
          </DialogPrimitive.Close>
        </div>
        {children}
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
}
