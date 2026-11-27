/** The nine Settings sections, in one menu (D-017). */
export const SETTINGS_SECTIONS = [
  {
    key: "search",
    label: "Search",
    about: "Job titles, places, minimum salary and notice period.",
  },
  { key: "agents", label: "Agents", about: "What runs while you are away." },
  {
    key: "ai",
    label: "AI models",
    about: "Which AI model is used and how much of the free limit is left.",
  },
  {
    key: "sources",
    label: "Sources and memory",
    about: "Watched companies, alerts and your rules.",
    href: "/settings/sources",
  },
  {
    key: "privacy",
    label: "Privacy",
    about: "What is stored, for how long, and what never leaves.",
  },
  { key: "safety", label: "Safety rules", about: "How scam signals are handled." },
  {
    key: "notifications",
    label: "Notifications",
    about: "The morning brief, alerts and quiet hours.",
  },
  {
    key: "accounts",
    label: "Accounts",
    about: "Your email, password, sessions, and exporting or deleting your data.",
  },
  {
    key: "connections",
    label: "Connections",
    about: "Gmail script, Google Calendar and tools that can read your data.",
  },
] as const;

export type SettingsKey = (typeof SETTINGS_SECTIONS)[number]["key"];

export function settingsHref(section: (typeof SETTINGS_SECTIONS)[number]): string {
  return "href" in section ? section.href : `/settings?section=${section.key}`;
}
