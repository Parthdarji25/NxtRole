import type { ReactNode } from "react";

import { Screen } from "@/components/layout/screen";
import { SettingsMenu } from "@/components/layout/settings-menu";
import { SETTINGS_SECTIONS } from "@/content/settings";
import { cn } from "@/lib/cn";

export type SettingsSection = (typeof SETTINGS_SECTIONS)[number];

/**
 * The Settings screen: the menu and one section. `chosen` is false on the phone's list view,
 * where the menu is shown alone.
 */
export function SettingsLayout({
  shown,
  chosen,
  children,
}: {
  shown: SettingsSection;
  chosen: boolean;
  children: ReactNode;
}) {
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
          {children}
        </section>
      </div>
    </Screen>
  );
}
