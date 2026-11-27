"use client";

import { Dialog as DialogPrimitive } from "radix-ui";
import type { ReactNode } from "react";

/** A small centred window for a question that needs an answer, such as confirming a deletion. */
export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;
export const DialogClose = DialogPrimitive.Close;

export function DialogContent({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="fixed inset-0 z-40 animate-fade-in bg-scrim" />
      <DialogPrimitive.Content className="fixed top-1/2 left-1/2 z-41 flex max-h-[85vh] w-[min(440px,calc(100vw-32px))] -translate-x-1/2 -translate-y-1/2 animate-fade-in flex-col gap-4 overflow-y-auto rounded-[var(--radius-hero)] border border-rule bg-paper p-6 text-ink shadow-overlay">
        <DialogPrimitive.Title className="heading text-2xl">{title}</DialogPrimitive.Title>
        <DialogPrimitive.Description className="text-ink-2">
          {description}
        </DialogPrimitive.Description>
        {children}
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
}
