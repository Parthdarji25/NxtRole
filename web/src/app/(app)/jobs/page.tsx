import type { Metadata } from "next";

import { Screen } from "@/components/layout/screen";
import { EmptyScreenState } from "@/components/states/EmptyScreenState";
import { EMPTY_STATES } from "@/content/emptyStates";

export const metadata: Metadata = { title: "Jobs" };

export default function JobsPage() {
  return (
    <Screen title="Jobs">
      <EmptyScreenState content={EMPTY_STATES.jobs} />
    </Screen>
  );
}
