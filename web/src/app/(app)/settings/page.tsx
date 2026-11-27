import type { Metadata } from "next";

import { Screen } from "@/components/layout/screen";
import { SettingsMenu } from "@/components/layout/settings-menu";
import { Button } from "@/components/ui/button";
import { SETTINGS_SECTIONS } from "@/content/settings";
import { cn } from "@/lib/cn";

export const metadata: Metadata = { title: "Settings" };

export default async function SettingsPage({
  searchParams,
}: {
  searchParams: Promise<{ section?: string | string[] }>;
}) {
  const { section: requested } = await searchParams;
  // Only a known section name is used; anything else shows the list.
  const chosen = SETTINGS_SECTIONS.find(
    (section) => section.key === requested && !("href" in section),
  );
  const shown = chosen ?? SETTINGS_SECTIONS[0];

  return (
    <Screen
      title="Settings"
      phoneLead={chosen ? undefined : "Everything NxtRole does on your behalf."}
      back={chosen ? { label: "Settings", href: "/settings" } : { label: "More", href: "/more" }}
    >
      <div className="flex flex-col gap-8 md:flex-row md:items-start">
        <SettingsMenu
          current={shown.key}
          // On phones the list and a chosen section are separate views.
          className={cn("md:w-[210px] md:shrink-0 md:gap-0.5", chosen && "hidden md:flex")}
        />
        <section
          aria-labelledby="section-title"
          className={cn("min-w-0 flex-1 flex-col gap-4", chosen ? "flex" : "hidden md:flex")}
        >
          <h2 id="section-title" className="heading text-[26px]">
            {shown.label}
          </h2>
          <p className="text-ink-2">{shown.about}</p>
          <p className="border-t border-rule pt-5 text-sm text-ink-3">Nothing to set here yet.</p>
          {shown.key === "accounts" && (
            <div className="flex flex-col items-start gap-3">
              <div className="flex flex-wrap gap-3">
                <Button disabled aria-describedby="data-note">
                  Export my data
                </Button>
                <Button disabled aria-describedby="data-note">
                  Delete my account and data
                </Button>
              </div>
              <p id="data-note" className="text-[13px] text-ink-3">
                These work once there is an account and data to act on.
              </p>
            </div>
          )}
        </section>
      </div>
    </Screen>
  );
}
