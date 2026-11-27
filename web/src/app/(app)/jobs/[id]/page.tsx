import type { Metadata } from "next";

import { Screen } from "@/components/layout/screen";
import { EmptyScreenState } from "@/components/states/EmptyScreenState";
import { EMPTY_STATES } from "@/content/emptyStates";

export const metadata: Metadata = { title: "Job" };

export default function JobPage() {
  return (
    <Screen kicker="Job detail and trust check" title="Job" back={{ label: "Jobs", href: "/jobs" }}>
      <EmptyScreenState content={EMPTY_STATES.job} />
    </Screen>
  );
}
