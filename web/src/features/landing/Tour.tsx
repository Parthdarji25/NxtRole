"use client";

import { Tabs as TabsPrimitive } from "radix-ui";
import { useEffect, useState, useSyncExternalStore } from "react";

import { Button } from "@/components/ui/button";
import { TOUR_STEPS } from "@/content/landing";
import { cn } from "@/lib/cn";

export const STEP_MILLISECONDS = 8000;
const REDUCED_MOTION = "(prefers-reduced-motion: reduce)";

function useReducedMotion(): boolean {
  return useSyncExternalStore(
    (onChange) => {
      const media = window.matchMedia(REDUCED_MOTION);
      media.addEventListener("change", onChange);
      return () => media.removeEventListener("change", onChange);
    },
    () => window.matchMedia(REDUCED_MOTION).matches,
    // While rendering on the server, assume less motion.
    () => true,
  );
}

/** "How it works": six steps that play on their own until the visitor takes over. */
export function Tour() {
  const [index, setIndex] = useState(0);
  // null: the visitor has not chosen; play unless they prefer reduced motion.
  const [choice, setChoice] = useState<boolean | null>(null);
  const reducedMotion = useReducedMotion();
  const playing = choice ?? !reducedMotion;

  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(
      () => setIndex((current) => (current + 1) % TOUR_STEPS.length),
      STEP_MILLISECONDS,
    );
    return () => window.clearInterval(timer);
  }, [playing]);

  /** Choosing a step yourself stops the automatic tour. */
  const goTo = (next: number) => {
    setChoice(false);
    setIndex((next + TOUR_STEPS.length) % TOUR_STEPS.length);
  };

  const step = TOUR_STEPS[index] ?? TOUR_STEPS[0]!;
  const following = TOUR_STEPS[(index + 1) % TOUR_STEPS.length]!;

  return (
    <TabsPrimitive.Root
      value={String(index)}
      onValueChange={(value) => goTo(Number(value))}
      className="flex flex-col gap-[18px]"
    >
      <TabsPrimitive.List
        aria-label="Steps"
        // Phones: pills that scroll to the screen edges. Desktop: six columns.
        className="flex gap-2 overflow-x-auto max-md:-mx-5 max-md:px-5 max-md:py-1 md:grid md:grid-cols-6 md:gap-0 md:border-t md:border-rule"
      >
        {TOUR_STEPS.map((entry, position) => (
          <TabsPrimitive.Trigger
            key={entry.name}
            value={String(position)}
            className={cn(
              "flex min-h-11 shrink-0 items-center rounded-full border border-rule-2 px-3.5 text-sm font-semibold whitespace-nowrap text-ink-2",
              "data-[state=active]:border-ink data-[state=active]:bg-ink data-[state=active]:text-paper",
              "md:-mt-px md:flex-col md:items-start md:gap-0.5 md:rounded-none md:border-0 md:border-t-[3px] md:border-transparent md:py-3 md:pr-4 md:pl-0 md:text-left",
              "focus-visible:-outline-offset-2 md:data-[state=active]:border-blue md:data-[state=active]:bg-transparent",
            )}
          >
            <span className="font-mono text-[11px] font-normal tracking-[0.08em] text-ink-3 max-md:hidden">
              {entry.time}
            </span>
            <span className="md:text-[15px] md:text-ink">
              <span aria-hidden="true" className="mr-1.5 font-mono font-normal md:text-ink-3">
                0{position + 1}
              </span>
              {entry.name}
            </span>
          </TabsPrimitive.Trigger>
        ))}
      </TabsPrimitive.List>

      <div className="grid overflow-hidden rounded-[18px] border border-rule bg-card shadow-panel md:rounded-[20px] lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        {/* The stage. Its colours are the mock's night sky in both themes. */}
        <div
          aria-hidden="true"
          className="relative flex min-h-[380px] flex-col justify-between gap-10 bg-[radial-gradient(120%_90%_at_50%_115%,#22307A_0%,#0D1130_52%,#07080F_100%)] p-6 text-white lg:min-h-[620px]"
        >
          <span className="font-mono text-[11px] tracking-[0.12em] uppercase opacity-75">
            {step.stage}
          </span>
          <span className="heading self-center text-[88px] leading-none opacity-90 lg:text-[160px]">
            0{index + 1}
          </span>
          <ul className="flex flex-wrap gap-2">
            {step.legend.map((item) => (
              <li
                key={item.label}
                className="inline-flex min-h-7 items-center gap-2 rounded-full border border-white/20 bg-[#0A0C1C]/55 px-3 text-xs"
              >
                <span className="size-2 rounded-full" style={{ background: item.dot }} />
                {item.label}
              </li>
            ))}
          </ul>
        </div>

        <TabsPrimitive.Content
          value={String(index)}
          // Announce changes only when the visitor is in control, not on every automatic step.
          aria-live={playing ? "off" : "polite"}
          className="flex min-w-0 flex-col gap-[18px] p-6 md:px-[34px] md:py-9"
        >
          <span className="font-mono text-[11px] tracking-[0.12em] text-blue uppercase">
            Step {index + 1} of {TOUR_STEPS.length} · {step.when}
          </span>
          <h3 className="heading text-[32px] md:text-[40px]">{step.title}</h3>
          <p className="text-base text-ink-2">{step.lead}</p>
          <div className="flex flex-col gap-2.5">
            <span className="kicker text-[11px]">What happens</span>
            <ol className="flex flex-col gap-2.5">
              {step.bullets.map((bullet, position) => (
                <li key={bullet} className="flex gap-3 text-[15px] leading-normal">
                  <span
                    aria-hidden="true"
                    className="inline-flex size-6 shrink-0 items-center justify-center rounded-full border border-rule-2 font-mono text-[11px] text-ink-2"
                  >
                    {position + 1}
                  </span>
                  <span>{bullet}</span>
                </li>
              ))}
            </ol>
          </div>
          <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 border-t border-rule pt-3.5 text-sm">
            <dt className="kicker pt-0.5 text-[11px]">Your part</dt>
            <dd className="font-semibold">{step.yourPart}</dd>
            <dt className="kicker pt-0.5 text-[11px]">Runs on</dt>
            <dd className="text-ink-2">{step.runsOn}</dd>
          </dl>
          <div className="mt-auto flex flex-wrap items-center gap-2 pt-1.5">
            <Button
              aria-label="Previous step"
              onClick={() => goTo(index - 1)}
              className="w-11 px-0"
            >
              ←
            </Button>
            <Button variant="primary" onClick={() => goTo(index + 1)} className="flex-1">
              {index === TOUR_STEPS.length - 1 ? "Start again" : `Next: ${following.name} →`}
            </Button>
            <Button onClick={() => setChoice(!playing)} className="text-[13px] text-ink-2">
              {playing ? "❚❚ Pause" : "▶ Play"}
            </Button>
          </div>
        </TabsPrimitive.Content>
      </div>
    </TabsPrimitive.Root>
  );
}
