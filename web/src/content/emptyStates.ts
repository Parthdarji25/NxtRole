/**
 * What each screen says when it has nothing to show (D-015). One place, so the wording can be
 * reviewed together. No example data: every text says what the state means and what to do next.
 */
export type EmptyContent = {
  /** The screen's address, for the review sheet. */
  route: string;
  title: string;
  body: string;
  /** The one blue action. */
  primary?: { label: string; href: string };
  secondary?: { label: string; href: string };
};

export const EMPTY_STATES = {
  today: {
    route: "/today",
    title: "No brief yet",
    body: "Add your resume and choose the companies to watch. Your first brief arrives at 7:00 AM.",
    primary: { label: "Set up your search", href: "/onboarding" },
    secondary: { label: "Watch companies", href: "/settings/sources" },
  },
  fresh: {
    route: "/today/fresh",
    title: "No fresh jobs right now",
    body: "When a strong new job appears, it shows here and you get one phone alert.",
    secondary: { label: "Back to Today", href: "/today" },
  },
  jobs: {
    route: "/jobs",
    title: "No jobs yet",
    body: "Add the companies you want to watch. New jobs are checked every hour from 7 AM to 9 PM.",
    primary: { label: "Watch companies", href: "/settings/sources" },
  },
  job: {
    route: "/jobs/[id]",
    title: "This job is not here",
    body: "It may have been removed, or the link is wrong.",
    secondary: { label: "Back to Jobs", href: "/jobs" },
  },
  ask: {
    route: "/ask",
    title: "What do you want to know?",
    body: "Ask about your jobs, pipeline, offers, notes or interviews. NxtRole looks things up and shows its sources. There is nothing to look up yet.",
    secondary: { label: "Browse jobs", href: "/jobs" },
  },
  pipeline: {
    route: "/pipeline",
    title: "Your pipeline is empty",
    body: "When you tap “I applied”, or add a job you already applied to, it appears here.",
    primary: { label: "Browse jobs", href: "/jobs" },
  },
  offer: {
    route: "/pipeline/offers/[id]",
    title: "No offer recorded",
    body: "Record an offer on its Pipeline card to see the monthly in-hand estimate and the clauses to ask about.",
    primary: { label: "Open Pipeline", href: "/pipeline" },
  },
  followUps: {
    route: "/follow-ups",
    title: "Nothing to follow up",
    body: "After you apply, reminders appear here on day 7 and day 14. NxtRole drafts them; you send them.",
    secondary: { label: "Open Pipeline", href: "/pipeline" },
  },
  prepareList: {
    route: "/prepare",
    title: "No interviews booked",
    body: "Add an interview round with a date on a Pipeline card. NxtRole then builds a brief to help you prepare.",
    primary: { label: "Open Pipeline", href: "/pipeline" },
  },
  prepare: {
    route: "/prepare/[applicationId]",
    title: "No brief for this interview",
    body: "A brief is built when a round has a date. Add the date on the Pipeline card.",
    secondary: { label: "Open Pipeline", href: "/pipeline" },
  },
  company: {
    route: "/companies/[id]",
    title: "No brief for this company",
    body: "Research runs for companies you watch or apply to, using public pages only.",
    secondary: { label: "Watch companies", href: "/settings/sources" },
  },
  studio: {
    route: "/studio",
    title: "Nothing to review",
    body: "Application packs and drafts appear here for you to check. Nothing leaves without your OK.",
    secondary: { label: "Browse jobs", href: "/jobs" },
  },
  pack: {
    route: "/studio/packs/[id]",
    title: "This pack is not here",
    body: "Make an application pack from a job. It waits here until you approve it.",
    secondary: { label: "Browse jobs", href: "/jobs" },
  },
  progress: {
    route: "/progress",
    title: "Not enough to show yet",
    body: "Your funnel and reply rate appear after you start applying.",
    secondary: { label: "Browse jobs", href: "/jobs" },
  },
  coach: {
    route: "/progress/coach",
    title: "No coach report yet",
    body: "The weekly coach starts once you have applications. Groups with fewer than 5 are marked “too few”.",
    secondary: { label: "Open Pipeline", href: "/pipeline" },
  },
  network: {
    route: "/network",
    title: "No connections imported",
    body: "Importing your LinkedIn Connections.csv will show who could refer you. Email addresses are dropped, and contacts are never sent to AI.",
    secondary: { label: "Browse jobs", href: "/jobs" },
  },
  sources: {
    route: "/settings/sources",
    title: "No watched companies yet",
    body: "Companies you add are checked for new jobs every hour from 7 AM to 9 PM, using their public job feeds only.",
    secondary: { label: "Back to Settings", href: "/settings" },
  },
} satisfies Record<string, EmptyContent>;

/** Short lines used inside a screen that has other content. */
export const QUIET_EMPTY = {
  pipelineStage: "Nothing in this stage yet.",
  filteredJobs: "Nothing matches these filters.",
  search: "Nothing found. Try a company, a skill or a word from a note.",
  agentLog: "Nothing has run yet. What NxtRole does while you are away will be listed here.",
} as const;
