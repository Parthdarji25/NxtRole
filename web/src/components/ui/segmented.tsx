"use client";

import { cn } from "@/lib/cn";

/** A small "one of these" control, as used for Light / Dark. */
export function Segmented<Value extends string>({
  label,
  options,
  value,
  onChange,
  className,
}: {
  label: string;
  options: ReadonlyArray<{ value: Value; label: string }>;
  value: Value | null;
  onChange: (value: Value) => void;
  className?: string;
}) {
  return (
    <div
      role="group"
      aria-label={label}
      className={cn(
        "grid auto-cols-fr grid-flow-col gap-0.5 rounded-lg border border-rule p-[3px]",
        className,
      )}
    >
      {options.map((option) => {
        const selected = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={selected}
            onClick={() => onChange(option.value)}
            className={cn(
              "hit-target min-h-[30px] rounded-md px-3 text-xs font-semibold",
              selected ? "bg-card text-ink shadow-[0_1px_2px_rgba(0,0,0,.08)]" : "text-ink-3",
            )}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
