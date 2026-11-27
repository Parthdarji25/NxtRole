import type { Metadata } from "next";

import { Logo } from "@/components/layout/logo";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { LoginForm } from "@/features/auth/LoginForm";

export const metadata: Metadata = { title: "Sign in" };

const POINTS = [
  "Agents read new jobs before you wake and score the best ones against your resume.",
  "Every morning, a short brief with the few worth applying to.",
  "Before every interview: rounds, likely questions and salary.",
];

/** The sunrise drawing from the phone mock. */
function Sunrise() {
  return (
    <svg viewBox="0 0 390 210" aria-hidden="true" className="mx-auto block h-[210px] max-w-full">
      <circle cx="195" cy="210" r="92" fill="var(--blue)" opacity="0.14" />
      <circle cx="195" cy="210" r="60" fill="var(--blue)" />
      <g stroke="var(--ink-3)" strokeWidth="1">
        <line x1="0" y1="186" x2="390" y2="186" />
        <line x1="40" y1="198" x2="350" y2="198" />
      </g>
      <g stroke="var(--blue)" strokeWidth="2" strokeLinecap="round">
        <line x1="195" y1="96" x2="195" y2="118" />
        <line x1="120" y1="128" x2="134" y2="142" />
        <line x1="270" y1="128" x2="256" y2="142" />
      </g>
    </svg>
  );
}

export default function LoginPage() {
  return (
    <main className="flex min-h-dvh flex-col md:flex-row">
      {/* Desktop: the editorial side */}
      <section className="hidden flex-[1_1_520px] flex-col gap-10 border-r border-rule bg-paper-2 px-14 py-10 md:flex">
        <Logo large className="self-start" />
        <div className="my-auto flex max-w-[520px] flex-col gap-7">
          <h1 className="heading animate-rise text-[44px] leading-none tracking-[-0.015em] lg:text-[64px]">
            Wake up to only the{" "}
            <em className="font-medium text-blue not-italic">jobs worth your time</em>, not five
            hundred.
          </h1>
          <ol className="flex flex-col border-t-2 border-ink">
            {POINTS.map((point, index) => (
              <li key={point} className="flex gap-4 border-b border-rule py-3.5">
                <span
                  aria-hidden="true"
                  className="heading min-w-[22px] text-[26px] leading-none text-ink-3"
                >
                  {index + 1}
                </span>
                <span className="text-ink-2">{point}</span>
              </li>
            ))}
          </ol>
        </div>
        <p className="text-[13px] text-ink-3">
          Free · works in your browser · nothing sent without your OK
        </p>
      </section>

      <section className="flex flex-[1_1_440px] flex-col px-6 py-4 md:py-10">
        <div className="flex items-center justify-between md:justify-end">
          <Logo className="md:hidden" />
          {/* The phone mock has no theme button here; the system setting applies. */}
          <span className="max-md:hidden">
            <ThemeToggle />
          </span>
        </div>
        <div className="-mx-6 mt-4 border-b border-rule md:hidden">
          <Sunrise />
        </div>
        <div className="mx-auto mt-6 flex w-full max-w-[400px] flex-col gap-[22px] md:my-auto">
          <div className="flex flex-col gap-2 md:hidden">
            <h1 className="heading text-[40px]">Wake up to the jobs worth your time.</h1>
            <p className="text-ink-2">Sign in to see your brief.</p>
          </div>
          <h2 className="heading hidden text-[40px] leading-none md:block">Sign in</h2>
          <LoginForm />
        </div>
      </section>
    </main>
  );
}
