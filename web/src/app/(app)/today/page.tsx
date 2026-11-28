import type { Metadata } from "next";

import { PhoneHeader } from "@/components/layout/phone-header";
import { TodayScreen } from "@/features/today/TodayScreen";
import { longDate } from "@/lib/dates";

export const metadata: Metadata = { title: "Today" };

export default function TodayPage() {
  return (
    <>
      <PhoneHeader />
      <TodayScreen kicker={`${longDate(new Date())} · your brief`} />
    </>
  );
}
