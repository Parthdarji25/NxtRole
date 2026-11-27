import type { Metadata } from "next";

import { Screen } from "@/components/layout/screen";
import { EmptyScreenState } from "@/components/states/EmptyScreenState";
import { EMPTY_STATES } from "@/content/emptyStates";

export const metadata: Metadata = { title: "Resume" };

export default function ResumePage() {
  return (
    <Screen
      title="Resume"
      lead="One master resume, tailored per job. Exports to LaTeX and PDF."
      back={{ label: "More", href: "/more" }}
    >
      <EmptyScreenState content={EMPTY_STATES.resume} />
    </Screen>
  );
}
