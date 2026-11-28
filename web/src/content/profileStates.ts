import type { EmptyContent } from "./emptyStates";

/** For the screens that work only from facts the owner has approved (FR-016). */
export const PROFILE_STATES = {
  needed: {
    route: "/resume",
    title: "Approve your profile first",
    body: "NxtRole only uses facts you have approved. Upload your resume, check what was found and approve it.",
    primary: { label: "Set up your profile", href: "/onboarding" },
  },
  ready: {
    route: "/resume",
    title: "Your facts are approved",
    body: "The resume builder arrives in a later update. It will use only the facts you approved.",
    secondary: { label: "Review your facts", href: "/onboarding" },
  },
} satisfies Record<string, EmptyContent>;
