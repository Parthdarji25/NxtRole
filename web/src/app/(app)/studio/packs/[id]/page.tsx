import type { Metadata } from "next";

import { Screen } from "@/components/layout/screen";
import { EmptyScreenState } from "@/components/states/EmptyScreenState";
import { EMPTY_STATES } from "@/content/emptyStates";

export const metadata: Metadata = { title: "Application pack" };

export default function PackPage() {
  return (
    <Screen
      kicker="Application pack"
      title="Application pack"
      back={{ label: "Studio", href: "/studio" }}
    >
      <EmptyScreenState content={EMPTY_STATES.pack} />
    </Screen>
  );
}
