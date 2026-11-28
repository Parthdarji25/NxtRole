import type { Metadata } from "next";

import { Screen } from "@/components/layout/screen";
import { EmptyScreenState } from "@/components/states/EmptyScreenState";
import { PROFILE_STATES } from "@/content/profileStates";
import { RequireProfile } from "@/features/profile/RequireProfile";

export const metadata: Metadata = { title: "Resume" };

export default function ResumePage() {
  return (
    <Screen
      title="Resume"
      lead="One master resume, tailored per job. Exports to LaTeX and PDF."
      back={{ label: "More", href: "/more" }}
    >
      <RequireProfile>
        <EmptyScreenState content={PROFILE_STATES.ready} />
      </RequireProfile>
    </Screen>
  );
}
