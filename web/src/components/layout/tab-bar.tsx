"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { CountBadge } from "@/components/ui/badge";
import { Icon } from "@/components/ui/icons";
import { cn } from "@/lib/cn";

import { activeTabKey, TABS, type NavCounts } from "./nav";

/** Phone tab bar, below 768px (MTabs mock, D-014). */
export function TabBar({ counts = {} }: { counts?: NavCounts }) {
  const active = activeTabKey(usePathname());
  return (
    <nav
      aria-label="Main"
      className="fixed inset-x-0 bottom-0 z-30 grid h-[84px] grid-cols-5 border-t border-rule bg-paper-2 px-2 pt-1.5 pb-[max(22px,env(safe-area-inset-bottom))] md:hidden"
    >
      {TABS.map((tab) => {
        const current = tab.key === active;
        const count = counts[tab.key];
        return (
          <Link
            key={tab.key}
            href={tab.href}
            aria-current={current ? "page" : undefined}
            className={cn(
              "flex min-h-[52px] flex-col items-center justify-center gap-[3px] no-underline",
              current
                ? "font-bold text-blue hover:text-blue"
                : "font-medium text-ink-3 hover:text-ink",
            )}
          >
            <span className="relative inline-flex">
              <Icon name={tab.icon} size={22} />
              {count && (
                <CountBadge
                  count={count.count}
                  urgent={count.urgent}
                  className="absolute -top-1.5 -right-3"
                />
              )}
            </span>
            <span className="text-[11px] tracking-[0.01em]">{tab.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
