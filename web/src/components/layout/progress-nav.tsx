import Link from "next/link";

import { cn } from "@/lib/cn";

const VIEWS = [
  { key: "overview", label: "Overview", href: "/progress" },
  { key: "coach", label: "Weekly coach", href: "/progress/coach" },
] as const;

/** The underline links shared by the Progress screens (Progress and Coach mocks). */
export function ProgressNav({ current }: { current: (typeof VIEWS)[number]["key"] }) {
  return (
    <nav aria-label="Progress views" className="flex gap-[22px] border-b border-rule">
      {VIEWS.map((view) => (
        <Link
          key={view.key}
          href={view.href}
          aria-current={view.key === current ? "page" : undefined}
          className={cn(
            "-mb-px inline-flex min-h-11 items-center border-b-2 text-sm font-semibold no-underline",
            view.key === current
              ? "border-ink text-ink hover:text-ink"
              : "border-transparent text-ink-3 hover:text-ink",
          )}
        >
          {view.label}
        </Link>
      ))}
    </nav>
  );
}
