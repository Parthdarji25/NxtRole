import type { Metadata } from "next";

import { Screen } from "@/components/layout/screen";
import { EmptyScreenState } from "@/components/states/EmptyScreenState";
import { EMPTY_STATES } from "@/content/emptyStates";

export const metadata: Metadata = { title: "Follow-ups" };

export default function FollowUpsPage() {
  return (
    <Screen
      title="Follow-ups"
      lead="NxtRole never sends email. Drafts use only what is in your pipeline and profile."
      back={{ label: "Pipeline", href: "/pipeline" }}
    >
      <EmptyScreenState content={EMPTY_STATES.followUps} />
    </Screen>
  );
}
