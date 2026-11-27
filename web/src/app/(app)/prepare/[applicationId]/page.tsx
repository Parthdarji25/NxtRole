import type { Metadata } from "next";

import { Screen } from "@/components/layout/screen";
import { EmptyScreenState } from "@/components/states/EmptyScreenState";
import { EMPTY_STATES } from "@/content/emptyStates";

export const metadata: Metadata = { title: "Interview prep" };

export default function PreparePage() {
  return (
    <Screen kicker="Interview prep" title="Prepare" back={{ label: "Prepare", href: "/prepare" }}>
      <EmptyScreenState content={EMPTY_STATES.prepare} />
    </Screen>
  );
}
