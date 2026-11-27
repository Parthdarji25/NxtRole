import type { Metadata } from "next";

import { Screen } from "@/components/layout/screen";
import { EmptyScreenState } from "@/components/states/EmptyScreenState";
import { EMPTY_STATES } from "@/content/emptyStates";

export const metadata: Metadata = { title: "Fresh jobs" };

export default function FreshJobsPage() {
  return (
    <Screen
      kicker="Fresh jobs"
      title="Fresh jobs"
      lead="Strong matches posted in the last hour."
      back={{ label: "Today", href: "/today" }}
    >
      <EmptyScreenState content={EMPTY_STATES.fresh} />
    </Screen>
  );
}
