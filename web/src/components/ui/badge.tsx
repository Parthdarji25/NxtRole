import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

export type Tone = "neutral" | "blue" | "green" | "amber" | "red";

const TONES: Record<Tone, string> = {
  neutral: "bg-paper-2 text-ink-2",
  blue: "bg-blue-soft text-blue-ink",
  green: "bg-green-soft text-green",
  amber: "bg-amber-soft text-amber",
  red: "bg-red-soft text-red-ink",
};

export function Badge({
  tone = "neutral",
  className,
  children,
}: {
  tone?: Tone;
  className?: string;
  children: ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold",
        TONES[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export type TrustLevel = "high" | "check" | "risky";

// The words carry the meaning; colour only supports them.
const TRUST: Record<TrustLevel, { label: string; tone: Tone }> = {
  high: { label: "High trust", tone: "green" },
  check: { label: "Check first", tone: "amber" },
  risky: { label: "Risky", tone: "red" },
};

export function TrustBadge({ level }: { level: TrustLevel }) {
  return <Badge tone={TRUST[level].tone}>{TRUST[level].label}</Badge>;
}

/** The number beside a menu item. Red only when something waits for the owner. */
export function CountBadge({
  count,
  urgent = false,
  className,
}: {
  count: number;
  urgent?: boolean;
  className?: string;
}) {
  if (count <= 0) return null;
  return (
    <span
      className={cn(
        "rounded-full px-[7px] font-mono text-[11px] leading-[18px]",
        urgent ? "bg-red text-paper" : "text-ink-3",
        className,
      )}
    >
      {count > 99 ? "99+" : count}
    </span>
  );
}
