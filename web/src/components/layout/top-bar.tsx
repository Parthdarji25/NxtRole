"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icons";

import { useShell } from "./shell-context";

const QUIET =
  "hit-target inline-flex h-[38px] items-center gap-2 rounded-lg border border-rule px-3 text-sm font-normal text-ink-2 no-underline";

/** Desktop top bar: search, Ask NxtRole and the agent log (TopBar mock). */
export function TopBar() {
  const { openSearch, openAgentLog } = useShell();
  return (
    <div className="hidden h-16 items-center gap-3 border-b border-rule px-7 md:flex">
      <button
        type="button"
        onClick={openSearch}
        aria-haspopup="dialog"
        aria-keyshortcuts="Control+K"
        className="hit-target flex h-[38px] min-w-0 flex-[0_1_380px] items-center gap-2.5 rounded-lg border border-rule bg-card px-3 text-left text-sm text-ink-3"
      >
        <Icon name="search" size={16} />
        <span className="flex-1 truncate">Search jobs, companies, notes, questions…</span>
        <kbd className="rounded border border-rule-2 px-1.5 font-mono text-[11px]">Ctrl K</kbd>
      </button>
      <div className="ml-auto flex items-center gap-2.5">
        <Button asChild variant="outline" className={QUIET}>
          <Link href="/ask">
            <Icon name="ask" size={16} />
            Ask NxtRole
          </Link>
        </Button>
        <button type="button" onClick={openAgentLog} aria-haspopup="dialog" className={QUIET}>
          <span aria-hidden="true" className="size-[7px] rounded-full bg-rule-2" />
          Agent log
        </button>
      </div>
    </div>
  );
}
