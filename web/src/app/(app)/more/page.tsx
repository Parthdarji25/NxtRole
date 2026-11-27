import type { Metadata } from "next";
import Link from "next/link";

import { Screen } from "@/components/layout/screen";
import { AgentStatusCard } from "@/components/layout/agent-status-card";
import { MORE_LINKS } from "@/components/layout/nav";
import { ThemeSwitch } from "@/components/layout/theme-switch";
import { Icon } from "@/components/ui/icons";
import { Kicker } from "@/components/ui/layout";

export const metadata: Metadata = { title: "More" };

/** The phone's menu for everything that is not in the tab bar (MMore mock). */
export default function MorePage() {
  return (
    <Screen title="More">
      <nav aria-label="More screens" className="flex flex-col border-t border-rule">
        {MORE_LINKS.map((link) => (
          <Link
            key={link.label}
            href={link.href}
            className="flex min-h-16 items-center gap-3.5 border-b border-rule px-1 text-ink no-underline hover:text-ink"
          >
            <Icon name={link.icon} size={20} />
            <span className="flex min-w-0 flex-1 flex-col">
              <span className="text-base font-semibold">{link.label}</span>
              <span className="text-[13px] text-ink-3">{link.hint}</span>
            </span>
            <span aria-hidden="true" className="text-xl text-ink-3">
              ›
            </span>
          </Link>
        ))}
      </nav>
      <section aria-labelledby="appearance" className="flex max-w-md flex-col gap-2.5">
        <h2 id="appearance">
          <Kicker>Appearance</Kicker>
        </h2>
        <ThemeSwitch className="rounded-xl p-1 [&>button]:min-h-11 [&>button]:text-sm" />
      </section>
      <AgentStatusCard />
      <Link href="/about" className="inline-flex min-h-11 items-center self-start text-sm">
        About NxtRole
      </Link>
    </Screen>
  );
}
