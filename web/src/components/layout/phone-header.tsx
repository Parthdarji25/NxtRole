"use client";

import { Icon } from "@/components/ui/icons";

import { Logo } from "./logo";
import { useShell } from "./shell-context";

/** The top of Today on phones (MToday mock): logo, search and the agent log. */
export function PhoneHeader() {
  const { openSearch, openAgentLog } = useShell();
  return (
    <div className="-mx-5 -mt-[22px] flex items-center justify-between gap-3 border-b border-rule px-5 py-3.5 md:hidden">
      <Logo />
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={openSearch}
          aria-label="Search"
          aria-haspopup="dialog"
          className="inline-flex size-11 items-center justify-center rounded-full border border-rule-2 bg-card text-ink-2"
        >
          <Icon name="search" size={18} />
        </button>
        <button
          type="button"
          onClick={openAgentLog}
          aria-haspopup="dialog"
          className="hit-target inline-flex h-10 items-center gap-2 rounded-full border border-rule-2 bg-card px-3.5 text-[13px] font-semibold text-ink-2"
        >
          <span aria-hidden="true" className="size-[7px] rounded-full bg-rule-2" />
          Agent log
        </button>
      </div>
    </div>
  );
}
