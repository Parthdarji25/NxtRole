import type { Metadata } from "next";
import Link from "next/link";

import { Logo } from "@/components/layout/logo";
import { Button } from "@/components/ui/button";
import { Kicker } from "@/components/ui/layout";
import { cn } from "@/lib/cn";

export const metadata: Metadata = { title: "Set up NxtRole" };

// The five steps of the Onboarding mock. Their forms arrive with the features they set up.
const STEPS = [
  {
    label: "Resume",
    title: "Start with your resume.",
    lead: "It’s how NxtRole scores jobs and tailors applications. Your name, phone and email are removed before any AI reads it.",
  },
  {
    label: "Profile",
    title: "What are you looking for?",
    lead: "Job titles, places and your minimum salary.",
  },
  {
    label: "Sources",
    title: "Where should we look?",
    lead: "Official job feeds and company careers pages. NxtRole never logs in to job sites.",
  },
  {
    label: "Inbox",
    title: "Let replies update your pipeline.",
    lead: "A short script in your own Google account sends job emails to NxtRole. You can skip this.",
  },
  {
    label: "Alerts",
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
    Number.isInteger(requested) && requested >= 1 && requested <= STEPS.length ? requested : 1;
  const current = STEPS[number - 1] ?? STEPS[0];
  const isFirst = number === 1;
  const isLast = number === STEPS.length;
  const nextHref = isLast ? "/today" : `/onboarding?step=${number + 1}`;

  return (
    <div className="mx-auto flex min-h-dvh max-w-[880px] flex-col">
      <header className="flex flex-col gap-3 px-6 pt-4 pb-3 md:gap-5 md:pt-8 md:pb-0">
        <div className="flex items-center justify-between gap-3 md:items-baseline">
          <Logo large className="max-md:hidden" />
          <Kicker>
            Step {number} of {STEPS.length}
            <span className="max-md:hidden"> · about 3 min</span>
          </Kicker>
          <Link
            href="/today"
            className="inline-flex min-h-11 items-center text-sm text-ink-2 no-underline hover:text-ink md:hidden"
          >
            Skip for now
          </Link>
        </div>
        <ol aria-label="Setup steps" className="grid grid-cols-5 gap-1 md:gap-2">
          {STEPS.map((entry, index) => (
            <li
              key={entry.label}
              aria-current={index + 1 === number ? "step" : undefined}
              className="flex flex-col gap-2"
            >
              <span
                aria-hidden="true"
                className={cn(
                  "h-1 rounded-full md:h-[3px]",
                  index < number ? "bg-blue" : "bg-rule",
                )}
              />
              {/* Phones show the bars only; the names stay available to screen readers. */}
              <span
                className={cn(
                  "text-[13px] max-md:sr-only",
                  index + 1 === number && "font-semibold text-ink",
                  index + 1 < number && "text-ink-2",
                  index + 1 > number && "text-ink-3",
                )}
              >
                {entry.label}
              </span>
            </li>
          ))}
        </ol>
      </header>

      <main className="flex flex-1 flex-col px-6 pt-3 pb-6 md:flex-none md:pt-12 md:pb-16">
        <div className="flex flex-col gap-4 md:gap-[22px]">
          <h1 className="heading text-[36px] leading-[1.05] md:text-[52px] md:leading-none">
            {current.title}
          </h1>
          <p className="max-w-[600px] text-ink-2">{current.lead}</p>
          <p className="border-y border-rule py-6 text-sm text-ink-3">
            This step is not ready yet.
          </p>
        </div>

        {/* Desktop buttons sit under the step; phone buttons stay at the bottom. */}
        <div className="mt-10 flex items-center justify-between border-t border-rule pt-5 max-md:hidden">
          {isFirst ? (
            <span />
          ) : (
            <Button asChild variant="text">
              <Link href={`/onboarding?step=${number - 1}`}>
                <span aria-hidden="true">←</span> Back
              </Link>
            </Button>
          )}
          <span className="flex items-center gap-4">
            {/* The last two steps are optional in the mock. */}
            {number >= 4 && (
              <Button asChild variant="text">
                <Link href={nextHref}>Skip for now</Link>
              </Button>
            )}
            <Button asChild variant="primary" size="lg">
              <Link href={nextHref}>{isLast ? "Finish setup" : "Continue"}</Link>
            </Button>
          </span>
        </div>
      </main>

      <div className="flex gap-2.5 border-t border-rule px-6 pt-3 pb-7 md:hidden">
        {!isFirst && (
          <Button asChild size="lg" className="min-h-[52px] rounded-xl">
            <Link href={`/onboarding?step=${number - 1}`}>Back</Link>
          </Button>
        )}
        <Button asChild variant="primary" size="lg" className="min-h-[52px] flex-1 rounded-xl">
          <Link href={nextHref}>
            {isLast ? "Finish" : isFirst ? "I’ll add it later" : "Continue"}
          </Link>
        </Button>
      </div>
    </div>
  );
}
