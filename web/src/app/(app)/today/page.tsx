import type { Metadata } from "next";

import { PhoneHeader } from "@/components/layout/phone-header";
import { Screen } from "@/components/layout/screen";
import { EmptyScreenState } from "@/components/states/EmptyScreenState";
import { EMPTY_STATES } from "@/content/emptyStates";
import { longDate } from "@/lib/dates";

export const metadata: Metadata = { title: "Today" };

export default function TodayPage() {
  return (
    <>
      <PhoneHeader />
      <Screen
        kicker={`${longDate(new Date())} · your brief`}
        title="Good morning."
        lead="Your short list appears here every morning."
      >
        <EmptyScreenState content={EMPTY_STATES.today} />
      </Screen>
    </>
  );
}
