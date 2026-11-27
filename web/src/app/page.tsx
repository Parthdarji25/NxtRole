import Link from "next/link";

import { Logo } from "@/components/layout/logo";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { Button } from "@/components/ui/button";
import { SAFETY_FACTS } from "@/content/landing";
import { Tour } from "@/features/landing/Tour";

const CONTAINER = "mx-auto w-full max-w-[1200px] px-5 md:px-6";
const NAV_LINK = "inline-flex min-h-11 items-center text-ink-2 no-underline hover:text-ink";

export default function LandingPage() {
  return (
    <>
      <header className="sticky top-0 z-10 border-b border-rule bg-paper/85 backdrop-blur-md">
        <div className={`${CONTAINER} flex h-[60px] items-center md:h-[68px] gap-2.5 md:gap-9`}>
          <Logo large />
          <nav aria-label="Primary" className="hidden gap-7 text-[15px] md:flex">
            <a href="#how" className={NAV_LINK}>
              How it works
            </a>
            <a href="#trust" className={NAV_LINK}>
              Is it safe?
            </a>
          </nav>
          <div className="ml-auto flex items-center gap-2.5">
            <ThemeToggle withIcon />
            <Button asChild variant="primary" size="sm" className="min-h-10 px-4 text-sm">
              <Link href="/login">
                {/* The phone mock uses the shorter label. */}
                <span className="md:hidden">Open app</span>
                <span className="max-md:hidden">Open the app</span>
              </Link>
            </Button>
          </div>
        </div>
      </header>

      <main>
        <section
          className={`${CONTAINER} flex flex-col gap-5 pt-11 pb-9 md:gap-7 md:pt-[84px] md:pb-14`}
        >
          <span className="kicker animate-rise">
            Your overnight job search<span className="max-md:hidden"> · free · just for you</span>
          </span>
          <h1 className="heading max-w-[1080px] animate-rise text-[clamp(52px,7.4vw,104px)] leading-[0.96] tracking-[-0.02em]">
            Sleep tonight. Wake up to{" "}
            <em className="font-medium text-blue not-italic">only the jobs worth applying to.</em>
          </h1>
          <div className="flex animate-rise flex-wrap items-end justify-between gap-7">
            <p className="max-w-[620px] text-[17px] leading-relaxed text-ink-2 md:text-[19px]">
              NxtRole is your personal job-search assistant. Before you wake, it checks official job
              feeds, removes the noise and scores the best jobs against your resume. At 7 AM you get
              a short list with the work already started. You make every final call.
            </p>
            <div className="flex flex-wrap gap-3 max-md:w-full">
              <Button
                asChild
                variant="ink"
                size="lg"
                className="min-h-[52px] px-[22px] max-md:w-full max-md:rounded-xl"
              >
                <a href="#how">
                  See how it works <span aria-hidden="true">↓</span>
                </a>
              </Button>
              {/* On phones the header button is enough (phone mock). */}
              <Button asChild size="lg" className="min-h-[52px] px-[22px] max-md:hidden">
                <Link href="/login">Open the app</Link>
              </Button>
            </div>
          </div>
        </section>

        <section
          id="how"
          aria-labelledby="how-title"
          className={`${CONTAINER} scroll-mt-20 pb-16 md:pb-[104px]`}
        >
          <div className="mb-[22px] flex flex-wrap items-end justify-between gap-6">
            <div className="flex flex-col gap-2.5">
              <span className="kicker">How it works</span>
              <h2 id="how-title" className="heading text-[38px] leading-none md:text-[52px]">
                One night<span className="max-md:hidden"> with NxtRole</span>, in six steps.
              </h2>
            </div>
            <p className="max-w-[340px] text-[15px] text-ink-3">
              <span className="md:hidden">Tap a step, or let it play.</span>
              <span className="max-md:hidden">The tour plays on its own, or pick any step.</span>
            </p>
          </div>
          <Tour />
        </section>

        <section
          id="trust"
          aria-labelledby="trust-title"
          className="scroll-mt-16 border-y border-rule bg-paper-2"
        >
          <div className={`${CONTAINER} flex flex-col gap-10 py-14 md:pt-[88px] md:pb-24`}>
            <div className="flex flex-col gap-2.5">
              <span className="kicker">Is it safe?</span>
              <h2 id="trust-title" className="heading text-[36px] leading-none md:text-[52px]">
                Three numbers to know before you start.
              </h2>
            </div>
            <ul className="grid md:grid-cols-3 md:border-t md:border-rule-2">
              {SAFETY_FACTS.map((fact) => (
                <li
                  key={fact.label}
                  className="flex gap-4 border-t border-rule-2 py-[18px] md:flex-col md:gap-3 md:border-t-0 md:px-7 md:py-7 md:first:pl-0 md:[&:not(:first-child)]:border-l"
                >
                  <span className="heading min-w-16 shrink-0 whitespace-nowrap text-[56px] leading-[0.9] text-blue md:min-w-0 md:text-[96px]">
                    {fact.number}
                  </span>
                  <span className="flex min-w-0 flex-col gap-1 md:gap-3">
                    <span className="text-base font-semibold md:text-lg">{fact.label}</span>
                    <span className="text-sm text-ink-2 md:text-[15px]">{fact.body}</span>
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className={`${CONTAINER} pt-14 md:pt-24`}>
          <div className="flex flex-col gap-5 rounded-[18px] bg-ink px-6 py-8 text-paper md:flex-row md:flex-wrap md:items-center md:justify-between md:gap-7 md:rounded-[20px] md:px-[52px] md:py-16">
            <h2 className="heading max-w-[680px] text-[36px] leading-none md:text-[56px]">
              Set it up tonight. Read your first brief at{" "}
              <em className="font-medium not-italic opacity-60">7 AM.</em>
            </h2>
            <Button
              asChild
              size="lg"
              className="min-h-[52px] border-paper bg-paper px-[26px] text-ink hover:bg-paper hover:text-ink max-md:rounded-xl md:min-h-[54px]"
            >
              <Link href="/login">
                Open the app <span aria-hidden="true">→</span>
              </Link>
            </Button>
          </div>
        </section>
      </main>

      <footer
        className={`${CONTAINER} flex flex-wrap items-center justify-between gap-3 py-7 text-[13px] text-ink-3 max-md:flex-col max-md:text-center`}
      >
        <span className="text-xl font-bold tracking-[-0.03em] text-ink">
          Nxt<span className="text-blue">Role</span>
        </span>
        <span>A personal project · Nothing is sent without your OK</span>
        <nav aria-label="Legal" className="flex gap-5">
          <Link href="/about" className={NAV_LINK}>
            About
          </Link>
          <Link href="/terms" className={NAV_LINK}>
            Terms
          </Link>
          <Link href="/privacy" className={NAV_LINK}>
            Privacy
          </Link>
        </nav>
      </footer>
    </>
  );
}
