import type { Metadata } from "next";

import { Screen } from "@/components/layout/screen";
import { EmptyScreenState } from "@/components/states/EmptyScreenState";
import { EMPTY_STATES } from "@/content/emptyStates";
import { RequireProfile } from "@/features/profile/RequireProfile";

export const metadata: Metadata = { title: "Studio" };

export default function StudioPage() {
  return (
    <Screen
      title="Studio"
      lead="Everything NxtRole wrote for you. Nothing leaves until you approve it."
      back={{ label: "More", href: "/more" }}
    >
      <RequireProfile>
        <EmptyScreenState content={EMPTY_STATES.studio} />
      </RequireProfile>
    </Screen>
  );
}
