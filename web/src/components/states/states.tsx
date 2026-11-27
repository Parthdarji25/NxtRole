/**
 * Loading, empty, error, offline and waiting states (D-015). None of them shows example data.
 * The style follows the few states the mocks draw: quiet text, hairlines and an amber band.
 */
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/cn";

// ---------------------------------------------------------------- Loading

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-shimmer rounded-md bg-rule", className)} />;
}

/** Wraps skeletons and tells screen readers that content is on its way. */
export function Loading({
  label = "Loading",
  className,
  children,
}: {
  label?: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <div role="status" aria-busy="true" className={className}>
      <span className="sr-only">{label}…</span>
      <div aria-hidden="true">{children}</div>
    </div>
  );
}

/** The list row of the mocks: numeral, title, meta, reason, action. */
export function ListSkeleton({ rows = 3, label }: { rows?: number; label?: string }) {
  return (
    <Loading label={label}>
      {Array.from({ length: rows }, (_, index) => (
        <div key={index} className="flex items-center gap-5 border-b border-rule py-5">
          <Skeleton className="hidden h-8 w-6 sm:block" />
          <div className="flex min-w-0 flex-1 flex-col gap-2.5">
            <Skeleton className="h-6 w-3/5" />
            <Skeleton className="h-3.5 w-4/5" />
            <Skeleton className="h-3.5 w-2/5" />
          </div>
          <Skeleton className="h-11 w-24 rounded-lg" />
        </div>
      ))}
    </Loading>
  );
}

export function PageSkeleton({ rows = 3, label }: { rows?: number; label?: string }) {
  return (
    <div className="flex flex-col gap-8">
      <div aria-hidden="true" className="flex flex-col gap-3 md:border-b-2 md:border-rule md:pb-6">
        <Skeleton className="h-3 w-40" />
        <Skeleton className="h-10 w-2/3 max-w-md md:h-14" />
        <Skeleton className="h-4 w-full max-w-lg" />
      </div>
      <ListSkeleton rows={rows} label={label} />
    </div>
  );
}

// ---------------------------------------------------------------- Empty and error

/** "Nothing here yet": what it means and the one thing to do next. */
export function EmptyState({
  title,
  children,
  action,
  className,
}: {
  title: string;
  children: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("flex flex-col items-start gap-3 border-y border-rule py-8", className)}>
      <h2 className="heading text-[22px]">{title}</h2>
      <p className="max-w-[560px] text-ink-2">{children}</p>
      {action && <div className="mt-1 flex flex-wrap gap-3">{action}</div>}
    </section>
  );
}

/** Something failed: say so plainly and offer to try again. */
export function ErrorState({
  title = "This did not load",
  children = "Check your connection and try again. Nothing you saved is lost.",
  onRetry,
  className,
}: {
  title?: string;
  children?: ReactNode;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <section
      role="alert"
      className={cn("flex flex-col items-start gap-3 border-y border-rule py-8", className)}
    >
      <span className="kicker text-red">Something went wrong</span>
      <h2 className="heading text-[22px]">{title}</h2>
      <p className="max-w-[560px] text-ink-2">{children}</p>
      {onRetry && (
        <Button className="mt-1" onClick={onRetry}>
          Try again
        </Button>
      )}
    </section>
  );
}

// ---------------------------------------------------------------- Banners

type BannerTone = "amber" | "red" | "blue" | "green";

const BANNERS: Record<BannerTone, { box: string; tag: string }> = {
  amber: { box: "bg-amber-soft", tag: "text-amber" },
  red: { box: "bg-red-soft", tag: "text-red-ink" },
  blue: { box: "bg-blue-soft", tag: "text-blue-ink" },
  green: { box: "bg-green-soft", tag: "text-green" },
};

/** The coloured band of the mocks ("SOURCE PAUSED …  Retry now"). */
export function Banner({
  tone = "amber",
  tag,
  children,
  action,
  className,
}: {
  tone?: BannerTone;
  tag: string;
  children: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div
      role="status"
      className={cn(
        "flex flex-wrap items-center gap-x-3.5 gap-y-2 rounded-[10px] px-3.5 py-2.5 text-sm text-ink",
        BANNERS[tone].box,
        className,
      )}
    >
      <span className={cn("font-mono text-xs tracking-[0.08em] uppercase", BANNERS[tone].tag)}>
        {tag}
      </span>
      <span className="min-w-0 flex-[1_1_240px]">{children}</span>
      {action}
    </div>
  );
}

export function OfflineNotice() {
  return (
    <Banner tone="amber" tag="Offline">
      You are offline. This is what was loaded last. Changes are switched off until you are back.
    </Banner>
  );
}

/** Work that waits, for example while the free AI limits are used up. */
export function PendingTag({ children = "Drafts pending" }: { children?: ReactNode }) {
  return <Badge tone="amber">{children}</Badge>;
}
