"use client";

import { useState, type ComponentProps } from "react";

import { Input } from "@/components/ui/field";

/** A password box with Show and Hide. */
export function PasswordInput({
  showLabel = "Show password",
  ...props
}: ComponentProps<"input"> & { showLabel?: string }) {
  const [shown, setShown] = useState(false);
  return (
    <div className="relative">
      <Input {...props} type={shown ? "text" : "password"} className="pr-20" />
      <button
        type="button"
        onClick={() => setShown((value) => !value)}
        aria-pressed={shown}
        aria-label={showLabel}
        className="absolute inset-y-0 right-0 min-w-16 rounded-r-[10px] px-3 text-[13px] font-semibold text-ink-2"
      >
        {shown ? "Hide" : "Show"}
      </button>
    </div>
  );
}
