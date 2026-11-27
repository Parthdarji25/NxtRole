import type { Metadata } from "next";

import { Screen } from "@/components/layout/screen";
import { SettingsMenu } from "@/components/layout/settings-menu";
import { EmptyScreenState } from "@/components/states/EmptyScreenState";
import { EMPTY_STATES } from "@/content/emptyStates";

export const metadata: Metadata = { title: "Sources and memory" };

export default function SourcesPage() {
  return (
    <Screen
      kicker="Settings · sources, alerts and memory"
      title="What NxtRole watches, and the rules it follows."
      phoneTitle="Sources and memory"
      lead="Your rules filter jobs before any AI runs. Nothing is learned without your OK, and every rule can be edited or deleted."
      back={{ label: "Settings", href: "/settings" }}
    >
      <div className="flex flex-col gap-8 md:flex-row md:items-start">
        <SettingsMenu
          current="sources"
          className="hidden md:flex md:w-[210px] md:shrink-0 md:gap-0.5"
        />
        <div className="flex min-w-0 flex-1 flex-col gap-6">
          <EmptyScreenState content={EMPTY_STATES.sources} />
          <section aria-labelledby="where" className="flex flex-col gap-2 text-sm">
            <h2 id="where" className="heading text-xl">
              Where jobs come from
            </h2>
            <p>Official job feeds: Greenhouse, Lever, Ashby, Adzuna and Arbeitnow.</p>
            <p>Job-alert emails read by the Gmail script in your own account.</p>
            <p>Jobs you add yourself.</p>
            <p className="font-semibold">
              Never: logging in to job sites or scraping pages behind a login.
            </p>
          </section>
        </div>
      </div>
    </Screen>
  );
}
