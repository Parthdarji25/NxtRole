import type { Metadata } from "next";

import { ProgressNav } from "@/components/layout/progress-nav";
import { Screen } from "@/components/layout/screen";
import { EmptyScreenState } from "@/components/states/EmptyScreenState";
import { EMPTY_STATES } from "@/content/emptyStates";

export const metadata: Metadata = { title: "Weekly coach" };

export default function CoachPage() {
  return (
    <Screen
      kicker="Weekly coach"
      title="Weekly coach"
      lead="One change for next week, from your own numbers."
      back={{ label: "More", href: "/more" }}
    >
      <ProgressNav current="coach" />
      <EmptyScreenState content={EMPTY_STATES.coach} />
    </Screen>
  );
}
