import type { Metadata } from "next";

import { Logo } from "@/components/layout/logo";
import { OfflineNotice } from "@/components/states/states";
import { PageHeader } from "@/components/ui/layout";

export const metadata: Metadata = { title: "Offline" };

/** Shown by the installed app when there is no connection (the service worker arrives in Phase 8). */
export default function OfflinePage() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-[720px] flex-col gap-7 px-5 py-8 md:px-10">
      <Logo className="self-start" />
      <PageHeader
        kicker="No connection"
        title="You are offline."
        lead="Connect to the internet and open the page again."
      />
      <OfflineNotice />
    </main>
  );
}
