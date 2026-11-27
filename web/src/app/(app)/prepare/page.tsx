import type { Metadata } from "next";

import { Screen } from "@/components/layout/screen";
import { EmptyScreenState } from "@/components/states/EmptyScreenState";
import { EMPTY_STATES } from "@/content/emptyStates";

export const metadata: Metadata = { title: "Prepare" };

export default function PrepareListPage() {
  return (
    <Screen title="Prepare" lead="Your upcoming interviews.">
      <EmptyScreenState content={EMPTY_STATES.prepareList} />
    </Screen>
  );
}
