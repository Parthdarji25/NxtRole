import Link from "next/link";
import type { ReactNode } from "react";

import { Logo } from "@/components/layout/logo";
import { Button, type ButtonProps } from "@/components/ui/button";
import { Kicker } from "@/components/ui/layout";
import { cn } from "@/lib/cn";

/** The five steps of the Onboarding mock. */
export const STEP_LABELS = ["Resume", "Profile", "Sources", "Inbox", "Alerts"] as const;

/** A footer button: either goes somewhere or does something. */
export type StepAction = {
  label: string;
  href?: string;
  onClick?: () => void;
  disabled?: boolean;
  busy?: boolean;
  /** Not the blue button, because the step itself holds the main action. */
  quiet?: boolean;
};

function ActionButton({
  action,
  children,
  ...style
}: {
  action: StepAction;
  children?: ReactNode;
} & Pick<ButtonProps, "variant" | "size" | "className">) {
  const content = children ?? action.label;
  if (action.href && !action.disabled) {
    return (
      <Button asChild {...style}>
        <Link href={action.href}>{content}</Link>
      </Button>
    );
  }
  return (
    <Button {...style} disabled={action.disabled} loading={action.busy} onClick={action.onClick}>
      {content}
    </Button>
  );
}

/** The header with the step bars, and the buttons under (desktop) or below (phone) a step. */
export function OnboardingFrame({
  step,
  back,
  skip,
  next,
  phoneBack = back,
  phoneNext = next,
  children,
}: {
  /** 1 to 5. */
  step: number;
  back?: StepAction;
  /** Only the optional steps have "Skip for now" on desktop. */
  skip?: StepAction;
  next: StepAction;
  /** Where the phone buttons differ from the desktop ones. */
  phoneBack?: StepAction;
  phoneNext?: StepAction;
  children: ReactNode;
}) {
  return (
    <div className="mx-auto flex min-h-dvh max-w-[880px] flex-col">
      <header className="flex flex-col gap-3 px-6 pt-4 pb-3 md:gap-5 md:pt-8 md:pb-0">
        <div className="flex items-center justify-between gap-3 md:items-baseline">
          <Logo large className="max-md:hidden" />
          <Kicker>
            Step {step} of {STEP_LABELS.length}
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
          {STEP_LABELS.map((label, index) => (
            <li
              key={label}
              aria-current={index + 1 === step ? "step" : undefined}
              className="flex flex-col gap-2"
            >
              <span
                aria-hidden="true"
                className={cn("h-1 rounded-full md:h-[3px]", index < step ? "bg-blue" : "bg-rule")}
              />
              {/* Phones show the bars only; the names stay available to screen readers. */}
              <span
                className={cn(
                  "text-[13px] max-md:sr-only",
                  index + 1 === step && "font-semibold text-ink",
                  index + 1 < step && "text-ink-2",
                  index + 1 > step && "text-ink-3",
                )}
              >
                {label}
              </span>
            </li>
          ))}
        </ol>
      </header>

      <main className="flex flex-1 flex-col px-6 pt-3 pb-6 md:flex-none md:pt-12 md:pb-16">
        {children}

        {/* Desktop buttons sit under the step; phone buttons stay at the bottom. */}
        <div className="mt-10 flex items-center justify-between border-t border-rule pt-5 max-md:hidden">
          {back ? (
            <ActionButton action={back} variant="text">
              <span aria-hidden="true">←</span> {back.label}
            </ActionButton>
          ) : (
            <span />
          )}
          <span className="flex items-center gap-4">
            {skip && <ActionButton action={skip} variant="text" />}
            <ActionButton action={next} variant={next.quiet ? "outline" : "primary"} size="lg" />
          </span>
        </div>
      </main>

      <div className="flex gap-2.5 border-t border-rule px-6 pt-3 pb-7 md:hidden">
        {phoneBack && (
          <ActionButton action={phoneBack} size="lg" className="min-h-[52px] rounded-xl" />
        )}
        <ActionButton
          action={phoneNext}
          variant={phoneNext.quiet ? "outline" : "primary"}
          size="lg"
          className="min-h-[52px] flex-1 rounded-xl"
        />
      </div>
    </div>
  );
}
