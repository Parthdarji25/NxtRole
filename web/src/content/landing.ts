/**
 * The landing page's words. The layout follows the Landing mock; every statement was rewritten
 * to be true for NxtRole (D-046), and the mock's example counts are left out.
 */
export type TourStep = {
  time: string;
  name: string;
  when: string;
  title: string;
  lead: string;
  bullets: readonly string[];
  yourPart: string;
  runsOn: string;
  /** The label and legend on the dark stage. */
  stage: string;
  legend: ReadonlyArray<{ label: string; dot: string }>;
};

export const TOUR_STEPS: readonly TourStep[] = [
  {
    time: "Once",
    name: "Set up",
    when: "Once · about 5 minutes",
    title: "Tell NxtRole what you want.",
    lead: "You set NxtRole up once. Your resume and wishes become the measure for every job.",
    bullets: [
      "Upload your resume. NxtRole reads your skills, experience and projects, and you approve them.",
      "Pick roles, cities, a salary floor and the companies you want to follow.",
      "Add the Gmail script in your own Google account, so job emails can update your tracker.",
    ],
    yourPart: "Five minutes, one time.",
    runsOn: "Your own private database",
    stage: "Profile · yours",
    legend: [{ label: "You: your resume and wishes", dot: "#8EA2FF" }],
  },
  {
    time: "Early + hourly",
    name: "Search",
    when: "Before you wake, then hourly",
    title: "It checks where jobs are posted.",
    lead: "Small agents read official job feeds and company careers pages before you wake, then every hour from 7 AM to 9 PM.",
    bullets: [
      "Official job feeds: Greenhouse, Lever, Ashby, Adzuna and Arbeitnow.",
      "Careers pages of the companies you follow, read straight from their job feeds.",
      "Your job-alert emails, and links you paste.",
    ],
    yourPart: "Nothing. Your laptop can be off.",
    runsOn: "GitHub Actions, in the cloud",
    stage: "New postings",
    legend: [
      { label: "Job feeds", dot: "#9FB2FF" },
      { label: "Careers pages", dot: "#F7CC80" },
      { label: "Gmail", dot: "#8CE6AE" },
      { label: "Links you paste", dot: "#FFFFFF" },
    ],
  },
  {
    time: "Each run",
    name: "Clean up",
    when: "Every run",
    title: "It throws out the noise.",
    lead: "Many postings are repeats, stale or unsafe. They are set aside before you ever see them.",
    bullets: [
      "The same job on several sites is merged into one.",
      "Jobs you already applied to are hidden.",
      "Jobs that ask for fees, use WhatsApp-only contact or hide the company are flagged as likely scams.",
    ],
    yourPart: "Nothing. You can still see what was hidden, and why.",
    runsOn: "Rules in NxtRole’s own code",
    stage: "New and real",
    legend: [
      { label: "Kept", dot: "#9FB2FF" },
      { label: "Removed: repeat, old or scam", dot: "#FF735F" },
    ],
  },
  {
    time: "Every morning",
    name: "Match",
    when: "Every morning",
    title: "It scores the best jobs against you.",
    lead: "The strongest candidates are read by AI and compared with your resume, with quotes from the job post as proof.",
    bullets: [
      "A score from 0 to 100, based on skills, experience, location and salary.",
      "A plain reason for each score: why it fits, and what is missing.",
      "A note if someone you know works there and could refer you.",
    ],
    yourPart: "Nothing.",
    runsOn: "Groq’s free AI",
    stage: "Strong matches",
    legend: [
      { label: "Strong match", dot: "#B8C6FF" },
      { label: "Weaker match", dot: "#7F86A3" },
    ],
  },
  {
    time: "7 AM",
    name: "Brief",
    when: "Every morning · 7:00 AM",
    title: "Your morning brief.",
    lead: "You wake up to a short list, not a feed: your top matches, best first, with the work already started.",
    bullets: [
      "Your top 5 strong matches, each with a trust check.",
      "Up to three high-trust jobs have an application pack ready for you to review.",
      "One alert on your phone.",
    ],
    yourPart: "Read it with your morning tea.",
    runsOn: "The NxtRole web app, with a phone alert",
    stage: "Your brief",
    legend: [{ label: "Job card, resume ready", dot: "#FBF9F4" }],
  },
  {
    time: "Daytime",
    name: "Apply & track",
    when: "When you are ready",
    title: "You decide. It keeps track.",
    lead: "Nothing is sent without your tap. Once you apply, NxtRole follows the job for you, all the way to an offer.",
    bullets: [
      "You apply on the company’s own site, using the tailored resume.",
      "A clear rejection or interview invite in your email moves the card, with undo. Anything else waits for your OK.",
      "A booked interview builds a prep brief: the rounds, likely questions and salary range.",
    ],
    yourPart: "Tap Apply, then prepare.",
    runsOn: "A script in your own Google account reads job emails",
    stage: "Applied · tracked",
    legend: [{ label: "Applied → Interview → Offer", dot: "#8EA2FF" }],
  },
];

export const SAFETY_FACTS = [
  {
    number: "₹0",
    label: "a month to run",
    body: "It runs on free cloud tiers: Vercel, Supabase, Upstash, GitHub Actions and Groq. No domain, no subscription, no card.",
  },
  {
    number: "1",
    label: "person can see it: you",
    body: "One account and one private database. A script in your own Google account sends only job emails, and you can export or delete everything.",
  },
  {
    number: "0",
    label: "things sent without your tap",
    body: "NxtRole drafts and you approve. It never applies, emails or messages anyone on its own, and runs no bots on LinkedIn or Naukri.",
  },
] as const;
