/** The menus, taken from the mocks (Nav, MTabs, MMore) and decisions D-014 and D-017. */
import type { IconName } from "@/components/ui/icons";

export type NavKey =
  | "today"
  | "ask"
  | "jobs"
  | "pipeline"
  | "followUps"
  | "prepare"
  | "studio"
  | "resume"
  | "network"
  | "progress"
  | "settings";

export type NavItem = { key: NavKey; label: string; href: string; icon: IconName };

export const SIDE_NAV: readonly NavItem[] = [
  { key: "today", label: "Today", href: "/today", icon: "today" },
  { key: "ask", label: "Ask NxtRole", href: "/ask", icon: "ask" },
  { key: "jobs", label: "Jobs", href: "/jobs", icon: "jobs" },
  { key: "pipeline", label: "Pipeline", href: "/pipeline", icon: "pipeline" },
  { key: "followUps", label: "Follow-ups", href: "/follow-ups", icon: "followUps" },
  { key: "prepare", label: "Prepare", href: "/prepare", icon: "prepare" },
  { key: "studio", label: "Studio", href: "/studio", icon: "studio" },
  { key: "resume", label: "Resume", href: "/resume", icon: "resume" },
  { key: "network", label: "Network", href: "/network", icon: "network" },
  { key: "progress", label: "Progress", href: "/progress", icon: "progress" },
];

export const SETTINGS_ITEM: NavItem = {
  key: "settings",
  label: "Settings",
  href: "/settings",
  icon: "settings",
};

function isUnder(pathname: string, base: string): boolean {
  return pathname === base || pathname.startsWith(`${base}/`);
}

/** Which side-menu item to highlight for an address. */
export function activeNavKey(pathname: string): NavKey | null {
  // A company brief is part of preparing (as in the CompanyBrief mock).
  if (isUnder(pathname, "/companies")) return "prepare";
  const item = [...SIDE_NAV, SETTINGS_ITEM].find((entry) => isUnder(pathname, entry.href));
  return item?.key ?? null;
}

export type TabKey = "today" | "jobs" | "pipeline" | "prepare" | "more";

export const TABS: ReadonlyArray<{ key: TabKey; label: string; href: string; icon: IconName }> = [
  { key: "today", label: "Today", href: "/today", icon: "today" },
  { key: "jobs", label: "Jobs", href: "/jobs", icon: "jobs" },
  { key: "pipeline", label: "Pipeline", href: "/pipeline", icon: "pipeline" },
  { key: "prepare", label: "Prepare", href: "/prepare", icon: "prepare" },
  { key: "more", label: "More", href: "/more", icon: "more" },
];

/** Which phone tab to highlight, following the tab shown in each phone mock. */
export function activeTabKey(pathname: string): TabKey {
  const key = activeNavKey(pathname);
  if (key === "today" || key === "jobs" || key === "pipeline" || key === "prepare") return key;
  if (key === "followUps") return "pipeline";
  return "more";
}

export const MORE_LINKS: ReadonlyArray<{
  label: string;
  hint: string;
  href: string;
  icon: IconName;
}> = [
  {
    label: "Ask NxtRole",
    hint: "Chat with your job search, with sources",
    href: "/ask",
    icon: "ask",
  },
  { label: "Follow-ups", hint: "Reminders that are due", href: "/follow-ups", icon: "followUps" },
  {
    label: "Network",
    hint: "People you know at your top matches",
    href: "/network",
    icon: "network",
  },
  { label: "Offer check", hint: "In-hand pay and clauses", href: "/pipeline", icon: "offer" },
  {
    label: "Weekly coach",
    hint: "What got replies this week",
    href: "/progress/coach",
    icon: "progress",
  },
  { label: "Studio", hint: "Drafts waiting for your review", href: "/studio", icon: "studio" },
  { label: "Resume", hint: "LaTeX export, ATS check, keywords", href: "/resume", icon: "resume" },
  {
    label: "Progress",
    hint: "What’s working and what to learn",
    href: "/progress",
    icon: "progress",
  },
  {
    label: "Sources and memory",
    hint: "Watched companies, alerts, your rules",
    href: "/settings/sources",
    icon: "sources",
  },
  {
    label: "Settings",
    hint: "Search, sources, alerts, privacy",
    href: "/settings",
    icon: "settings",
  },
];

/** Counts beside menu items. Empty until later phases provide real numbers. */
export type NavCounts = Partial<Record<NavKey | "more", { count: number; urgent?: boolean }>>;
