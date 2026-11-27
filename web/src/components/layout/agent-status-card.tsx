"use client";

import { Panel } from "@/components/ui/layout";

import { useShell } from "./shell-context";

export function AgentStatusCard() {
  const { openAgentLog } = useShell();
  return (
    <Panel className="flex max-w-md flex-col gap-2 p-4">
      <span className="flex items-center gap-2 font-semibold">
        <span aria-hidden="true" className="size-2 rounded-full bg-rule-2" />
        Agents are not set up yet
      </span>
      <span className="text-sm text-ink-2">
        Searching will run in the cloud, so your phone can stay asleep.
      </span>
      <button
        type="button"
        onClick={openAgentLog}
        aria-haspopup="dialog"
        className="inline-flex min-h-11 items-center self-start text-sm font-semibold text-blue"
      >
        See the agent log <span aria-hidden="true">&nbsp;→</span>
      </button>
    </Panel>
  );
}
