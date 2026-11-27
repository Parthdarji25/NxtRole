import type { Metadata } from "next";

import { Screen } from "@/components/layout/screen";
import { EmptyScreenState } from "@/components/states/EmptyScreenState";
import { EMPTY_STATES } from "@/content/emptyStates";

export const metadata: Metadata = { title: "Company brief" };

export default function CompanyBriefPage() {
  return (
    <Screen
      kicker="Company brief"
      title="Company brief"
      back={{ label: "Prepare", href: "/prepare" }}
    >
      <EmptyScreenState content={EMPTY_STATES.company} />
    </Screen>
  );
}
