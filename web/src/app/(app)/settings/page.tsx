import type { Metadata } from "next";
import type { ReactNode } from "react";

import { SettingsLayout } from "@/components/layout/settings-layout";
import { SETTINGS_SECTIONS, type SettingsKey } from "@/content/settings";
import { AccountSettings } from "@/features/account/AccountSettings";
import { SearchSettingsContainer } from "@/features/preferences/SearchSettingsContainer";
import { PrivacyContainer } from "@/features/privacy/PrivacyContainer";

export const metadata: Metadata = { title: "Settings" };

/** The sections that can be used. The others arrive with the features they set. */
const SECTIONS: Partial<Record<SettingsKey, ReactNode>> = {
  search: <SearchSettingsContainer />,
  privacy: <PrivacyContainer />,
  accounts: <AccountSettings />,
};

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
    <SettingsLayout shown={shown} chosen={Boolean(chosen)}>
      {SECTIONS[shown.key] ?? (
        <p className="border-t border-rule pt-5 text-sm text-ink-3">Nothing to set here yet.</p>
      )}
    </SettingsLayout>
  );
}
