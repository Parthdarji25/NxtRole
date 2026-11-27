import type { Metadata } from "next";

import { Screen } from "@/components/layout/screen";
import { EmptyScreenState } from "@/components/states/EmptyScreenState";
import { EMPTY_STATES } from "@/content/emptyStates";

export const metadata: Metadata = { title: "Network" };

export default function NetworkPage() {
  return (
    <Screen
      title="Network"
      lead="Find who could refer you."
      back={{ label: "More", href: "/more" }}
    >
      <EmptyScreenState content={EMPTY_STATES.network} />
    </Screen>
  );
}
