import type { Metadata } from "next";

import { SettingsLayout } from "@/components/layout/settings-layout";
import { SETTINGS_SECTIONS } from "@/content/settings";
import { AccountSettings } from "@/features/account/AccountSettings";

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
    <SettingsLayout shown={shown} chosen={Boolean(chosen)}>
      {shown.key === "accounts" ? (
        <AccountSettings />
      ) : (
        <p className="border-t border-rule pt-5 text-sm text-ink-3">Nothing to set here yet.</p>
      )}
    </SettingsLayout>
  );
}
