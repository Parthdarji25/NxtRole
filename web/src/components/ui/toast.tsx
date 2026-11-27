"use client";

import { Toaster as Sonner, toast } from "sonner";

const UNDO_MILLISECONDS = 8000;

/** Short messages at the bottom of the screen. Screen readers announce them politely. */
export function Toaster() {
  return (
    <Sonner
      position="bottom-center"
      // Above the phone tab bar.
      mobileOffset={{ bottom: 96 }}
      toastOptions={{
        unstyled: true,
        classNames: {
          toast:
            "flex w-full items-center justify-between gap-4 rounded-[var(--radius-panel)] bg-ink px-4 py-3 text-sm text-paper shadow-overlay",
          title: "font-medium",
          actionButton:
            "hit-target shrink-0 rounded-md border border-paper/40 px-3 py-1.5 text-[13px] font-semibold",
        },
      }}
    />
  );
}

export function showToast(message: string): void {
  toast(message);
}

/** A message with an Undo button, for every change the owner may want to reverse. */
export function showUndoToast(message: string, onUndo: () => void): void {
  toast(message, { duration: UNDO_MILLISECONDS, action: { label: "Undo", onClick: onUndo } });
}
