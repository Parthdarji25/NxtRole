import type { ComponentProps, ReactNode } from "react";

import { cn } from "@/lib/cn";

export function Kicker({ className, ...props }: ComponentProps<"span">) {
  return <span className={cn("kicker", className)} {...props} />;
}

/** The top of every screen: mono label, large heading, one sentence, 2px ink rule. */
export function PageHeader({
  kicker,
  title,
  lead,
  phoneTitle,
  phoneLead,
  actions,
  className,
}: {
  kicker?: string;
  title: string;
  lead?: ReactNode;
  /** A shorter title or an extra sentence that only the phone mock shows. */
  phoneTitle?: string;
  phoneLead?: string;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <header
      className={cn(
        "flex flex-wrap items-end justify-between gap-4 pb-1",
        "md:border-b-2 md:border-ink md:pb-[22px]",
        className,
      )}
    >
      <div className="flex min-w-0 flex-col gap-2 md:gap-2.5">
        {kicker && <Kicker>{kicker}</Kicker>}
        <h1
          className={cn(
            "heading text-[40px] tracking-[-0.01em] md:text-[56px] md:leading-none",
            phoneTitle && "max-md:text-[30px]",
          )}
        >
          {phoneTitle ? (
            <>
              <span className="md:hidden">{phoneTitle}</span>
              <span className="max-md:hidden">{title}</span>
            </>
          ) : (
            title
          )}
        </h1>
        {phoneLead && <p className="text-sm text-ink-2 md:hidden">{phoneLead}</p>}
        {lead && <p className="max-w-[680px] text-base text-ink-2 md:text-lg">{lead}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-3">{actions}</div>}
    </header>
  );
}

export function SectionHeading({
  title,
  aside,
  className,
}: {
  title: string;
  aside?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-wrap items-baseline justify-between gap-3", className)}>
      <h2 className="heading text-[26px] md:text-[30px]">{title}</h2>
      {aside && <div className="text-[13px] text-ink-3">{aside}</div>}
    </div>
  );
}

/** A card. The mocks use them sparingly: "rules, not boxes". */
export function Panel({
  raised = false,
  className,
  ...props
}: ComponentProps<"div"> & { raised?: boolean }) {
  return (
    <div
      className={cn(
        "rounded-[var(--radius-panel)] border border-rule bg-card p-[22px]",
        raised && "shadow-panel",
        className,
      )}
      {...props}
    />
  );
}

export function StatTile({
  value,
  label,
  className,
}: {
  value: string;
  label: string;
  className?: string;
}) {
  return (
    <div className={cn("flex min-w-0 flex-col gap-1", className)}>
      <span className="heading text-[28px]">{value}</span>
      <span className="text-[13px] text-ink-3">{label}</span>
    </div>
  );
}

export function ProgressBar({
  value,
  max,
  label,
  className,
}: {
  value: number;
  max: number;
  label: string;
  className?: string;
}) {
  const safeMax = Math.max(max, 1);
  const safeValue = Math.min(Math.max(value, 0), safeMax);
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={safeMax}
      aria-valuenow={safeValue}
      className={cn("h-[3px] w-full overflow-hidden rounded-full bg-rule", className)}
    >
      <div
        className="h-full bg-ink transition-[width] duration-450"
        style={{ width: `${(safeValue / safeMax) * 100}%` }}
      />
    </div>
  );
}
