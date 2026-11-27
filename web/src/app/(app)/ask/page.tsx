import type { Metadata } from "next";

import { Screen } from "@/components/layout/screen";
import { EmptyScreenState } from "@/components/states/EmptyScreenState";
import { EMPTY_STATES } from "@/content/emptyStates";

export const metadata: Metadata = { title: "Ask NxtRole" };

export default function AskPage() {
  return (
    <Screen
      title="Ask NxtRole"
      lead="Answers come from your own jobs, pipeline, notes and interview log, with sources. Any change waits for your approval."
      back={{ label: "More", href: "/more" }}
    >
      <EmptyScreenState content={EMPTY_STATES.ask} />
    </Screen>
  );
}
