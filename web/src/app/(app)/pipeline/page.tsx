import type { Metadata } from "next";

import { Screen } from "@/components/layout/screen";
import { EmptyScreenState } from "@/components/states/EmptyScreenState";
import { EMPTY_STATES } from "@/content/emptyStates";

export const metadata: Metadata = { title: "Pipeline" };

export default function PipelinePage() {
  return (
    <Screen title="Pipeline">
      <EmptyScreenState content={EMPTY_STATES.pipeline} />
    </Screen>
  );
}
