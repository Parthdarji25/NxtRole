"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { CountBadge } from "@/components/ui/badge";
import { Icon } from "@/components/ui/icons";
import { cn } from "@/lib/cn";

import { Logo } from "./logo";
import { activeNavKey, SETTINGS_ITEM, SIDE_NAV, type NavCounts, type NavItem } from "./nav";
import { ThemeSwitch } from "./theme-switch";

function NavLink({
  item,
  active,
  count,
}: {
  item: NavItem;
  active: boolean;
  count?: { count: number; urgent?: boolean };
}) {
  return (
    <Link
      href={item.href}
      aria-current={active ? "page" : undefined}
      title={item.label}
      className={cn(
        "hit-target flex min-h-11 items-center gap-3 rounded-lg px-3 text-[15px] no-underline",
        "transition-colors duration-150 md:justify-center lg:min-h-10 lg:justify-start",
        active
          ? "bg-card font-semibold text-ink shadow-[inset_2px_0_0_var(--blue)] hover:text-ink"
          : "font-medium text-ink-2 hover:bg-card hover:text-ink",
      )}
    >
      <Icon name={item.icon} />
      {/* Hidden from sight (not from screen readers) when only icons fit. */}
      <span className="flex-1 md:sr-only lg:not-sr-only">{item.label}</span>
      {count && (
        <CountBadge
          count={count.count}
          urgent={count.urgent}
          className="md:absolute md:top-0.5 md:right-0.5 lg:static"
        />
      )}
    </Link>
  );
}

/** Desktop side menu: 260px, icons only between 768px and 1023px (D-014). */
export function SideNav({ counts = {} }: { counts?: NavCounts }) {
  const active = activeNavKey(usePathname());
  return (
    <div className="hidden w-[76px] shrink-0 border-r border-rule bg-paper-2 md:block lg:w-[260px]">
      <div className="sticky top-0 flex h-dvh flex-col gap-5 overflow-y-auto px-3.5 py-5">
        <Logo compact className="self-center px-2.5 lg:self-start" />
        <nav aria-label="Main" className="flex flex-col gap-0.5">
          {SIDE_NAV.map((item) => (
            <NavLink
              key={item.key}
              item={item}
              active={active === item.key}
              count={counts[item.key]}
            />
          ))}
        </nav>
        <div className="mt-auto flex flex-col gap-3">
          <NavLink item={SETTINGS_ITEM} active={active === "settings"} />
          <p className="flex items-center gap-2.5 border-t border-rule px-3 py-2.5 text-xs text-ink-3 md:justify-center lg:justify-start">
            <span aria-hidden="true" className="size-[7px] shrink-0 rounded-full bg-rule-2" />
            <span className="md:sr-only lg:not-sr-only">Agents are not set up yet</span>
          </p>
          <ThemeSwitch className="md:grid-flow-row lg:grid-flow-col" />
        </div>
      </div>
    </div>
  );
}
