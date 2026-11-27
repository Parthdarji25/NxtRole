import type { Metadata } from "next";

import { ProgressNav } from "@/components/layout/progress-nav";
import { Screen } from "@/components/layout/screen";
import { EmptyScreenState } from "@/components/states/EmptyScreenState";
import { EMPTY_STATES } from "@/content/emptyStates";

export const metadata: Metadata = { title: "Progress" };

export default function ProgressPage() {
  return (
    <Screen
      title="Progress"
      lead="What is working and what to learn."
      back={{ label: "More", href: "/more" }}
    >
      <ProgressNav current="overview" />
      <EmptyScreenState content={EMPTY_STATES.progress} />
    </Screen>
  );
}
