import type { Metadata } from "next";

import { Screen } from "@/components/layout/screen";
import { EmptyScreenState } from "@/components/states/EmptyScreenState";
import { EMPTY_STATES } from "@/content/emptyStates";

export const metadata: Metadata = { title: "Offer check" };

export default function OfferCheckPage() {
  return (
    <Screen
      kicker="Offer check"
      title="Offer check"
      back={{ label: "Pipeline", href: "/pipeline" }}
    >
      <EmptyScreenState content={EMPTY_STATES.offer} />
    </Screen>
  );
}
