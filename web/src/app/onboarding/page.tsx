import type { Metadata } from "next";

import { OnboardingFrame, STEP_LABELS } from "@/features/onboarding/OnboardingFrame";

export const metadata: Metadata = { title: "Set up NxtRole" };

// The headings of the Onboarding mock. The forms arrive with the features they set up.
const HEADINGS = [
  {
    title: "Start with your resume.",
    lead: "It’s how NxtRole scores jobs and tailors applications. Your name, phone and email are removed before any AI reads it.",
  },
  {
    title: "What are you looking for?",
    lead: "Job titles, places and your minimum salary.",
  },
  {
    title: "Where should we look?",
    lead: "Official job feeds and company careers pages. NxtRole never logs in to job sites.",
  },
  {
    title: "Let replies update your pipeline.",
    lead: "A short script in your own Google account sends job emails to NxtRole. You can skip this.",
  },
  {
    title: "When should we tell you?",
    lead: "One brief a day. Alerts only when it can’t wait.",
  },
] as const;

export default async function OnboardingPage({
  searchParams,
}: {
  searchParams: Promise<{ step?: string | string[] }>;
}) {
  const { step } = await searchParams;
  const requested = Number(step);
  // Anything that is not a whole number from 1 to 5 starts at the first step.
  const number =
    Number.isInteger(requested) && requested >= 1 && requested <= STEP_LABELS.length
      ? requested
      : 1;
  const current = HEADINGS[number - 1] ?? HEADINGS[0];
  const isFirst = number === 1;
  const isLast = number === STEP_LABELS.length;
  const nextHref = isLast ? "/today" : `/onboarding?step=${number + 1}`;
  const back = isFirst ? undefined : { label: "Back", href: `/onboarding?step=${number - 1}` };

  return (
    <OnboardingFrame
      step={number}
      back={back}
      // The last two steps are optional in the mock.
      skip={number >= 4 ? { label: "Skip for now", href: nextHref } : undefined}
      next={{ label: isLast ? "Finish setup" : "Continue", href: nextHref }}
      phoneNext={{
        label: isLast ? "Finish" : isFirst ? "I’ll add it later" : "Continue",
        href: nextHref,
      }}
    >
      <div className="flex flex-col gap-4 md:gap-[22px]">
        <h1 className="heading text-[36px] leading-[1.05] md:text-[52px] md:leading-none">
          {current.title}
        </h1>
        <p className="max-w-[600px] text-ink-2">{current.lead}</p>
        <p className="border-y border-rule py-6 text-sm text-ink-3">This step is not ready yet.</p>
      </div>
    </OnboardingFrame>
  );
}
