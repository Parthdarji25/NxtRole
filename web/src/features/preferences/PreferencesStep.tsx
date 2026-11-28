"use client";

import { useState } from "react";

import { Chip } from "@/components/ui/chip";
import { Input } from "@/components/ui/field";
import { FormProblem } from "@/components/ui/form-problem";
import { AddItem } from "@/components/ui/tag-input";
import { cn } from "@/lib/cn";

import { stepPay, type Draft, type DraftErrors } from "./draft";

/** The chips of one choice: what is suggested and what the owner added. */
function Choices({
  label,
  addLabel,
  suggested,
  chosen,
  onChange,
  error,
  className,
}: {
  label: string;
  addLabel: string;
  suggested: string[];
  chosen: string[];
  onChange: (chosen: string[]) => void;
  error?: string;
  className?: string;
}) {
  // A choice that is switched off stays in view, so it can be switched on again.
  const [seen, setSeen] = useState(() => [...new Set([...chosen, ...suggested])]);
  const all = [...new Set([...seen, ...chosen])];

  return (
    <div
      role="group"
      aria-label={label}
      className={cn("flex flex-col gap-2.5 border-rule md:border-t md:py-[18px]", className)}
    >
      <span className="font-semibold max-md:sr-only">{label}</span>
      <div className="flex flex-wrap items-center gap-2">
        {all.map((item) => (
          <Chip
            key={item}
            look="ink"
            pressed={chosen.includes(item)}
            onPressedChange={(on) =>
              onChange(on ? [...chosen, item] : chosen.filter((other) => other !== item))
            }
          >
            {item}
          </Chip>
        ))}
        <AddItem
          label={addLabel}
          onAdd={(value) => {
            const known = all.find((item) => item.toLowerCase() === value.toLowerCase());
            const item = known ?? value;
            setSeen((now) => [...new Set([...now, item])]);
            if (!chosen.includes(item)) onChange([...chosen, item]);
          }}
        />
      </div>
      <FormProblem>{error ?? null}</FormProblem>
    </div>
  );
}

function Salary({
  value,
  onChange,
  error,
}: {
  value: string;
  onChange: (value: string) => void;
  error?: string;
}) {
  return (
    <div className="flex flex-col gap-2 border-rule md:border-y md:py-[18px]">
      <div className="flex flex-col gap-2 md:flex-row md:flex-wrap md:items-center md:justify-between md:gap-4">
        <label htmlFor="min-salary" className="flex flex-col">
          <span className="font-semibold">Minimum salary</span>
          <span className="text-[13px] text-ink-3">Jobs below this are hidden</span>
        </label>
        <span className="flex items-center gap-4 md:gap-2">
          <button
            type="button"
            aria-label="Lower the minimum salary"
            onClick={() => onChange(stepPay(value, -1))}
            className="size-12 shrink-0 rounded-xl border border-rule-2 text-[22px] md:hidden"
          >
            <span aria-hidden="true">−</span>
          </button>
          <span className="flex flex-1 items-center justify-center gap-2">
            <span aria-hidden="true">₹</span>
            <Input
              id="min-salary"
              inputMode="decimal"
              value={value}
              placeholder="Not set"
              aria-invalid={error ? true : undefined}
              onChange={(event) => onChange(event.target.value)}
              className="h-12 w-28 text-center text-[22px] md:h-11 md:w-[90px] md:text-left md:text-[15px]"
            />
            <span>LPA</span>
          </span>
          <button
            type="button"
            aria-label="Raise the minimum salary"
            onClick={() => onChange(stepPay(value, 1))}
            className="size-12 shrink-0 rounded-xl border border-rule-2 text-[22px] md:hidden"
          >
            <span aria-hidden="true">+</span>
          </button>
        </span>
      </div>
      <FormProblem>{error ?? null}</FormProblem>
    </div>
  );
}

/**
 * Onboarding step 2. Desktop shows everything on one page; phones show the roles first, then
 * places and pay, as in the two mocks.
 */
export function PreferencesStep({
  draft,
  onChange,
  errors,
  suggestions,
  phonePart,
}: {
  draft: Draft;
  onChange: (draft: Draft) => void;
  errors: DraftErrors;
  /** Taken from the approved profile; empty when there is none. */
  suggestions: { titles: string[]; places: string[] };
  /** Which of the two phone views is open. */
  phonePart: "roles" | "pay";
}) {
  const fromResume = suggestions.titles.length > 0 || suggestions.places.length > 0;
  const set = (part: Partial<Draft>) => onChange({ ...draft, ...part });

  return (
    <div className="flex flex-col gap-4 md:gap-1.5">
      <h1 className="heading text-[36px] leading-[1.05] md:mb-2 md:text-[52px] md:leading-none">
        <span className="max-md:hidden">What are you looking for?</span>
        <span className="md:hidden">
          {phonePart === "roles" ? "Which roles should we look for?" : "Where, and for how much?"}
        </span>
      </h1>
      <p className="text-ink-2 max-md:hidden md:mb-4">
        {fromResume
          ? "We filled this in from your resume. Change anything."
          : "Tell NxtRole what to look for. You can change it any time in Settings."}
      </p>
      {phonePart === "roles" && (
        <p className="text-ink-2 md:hidden">
          {fromResume ? "Suggested from your resume. Pick any number." : "Add any number."}
        </p>
      )}

      <Choices
        label="Job titles"
        addLabel="Add a title"
        suggested={suggestions.titles}
        chosen={draft.titles}
        onChange={(titles) => set({ titles })}
        error={errors.titles}
        className={cn(phonePart !== "roles" && "max-md:hidden")}
      />
      <div className={cn("flex flex-col gap-4 md:gap-0", phonePart !== "pay" && "max-md:hidden")}>
        <Choices
          label="Where"
          addLabel="Add a place"
          suggested={suggestions.places}
          chosen={draft.places}
          onChange={(places) => set({ places })}
          error={errors.places}
        />
        <Salary
          value={draft.min_salary_lpa}
          onChange={(min_salary_lpa) => set({ min_salary_lpa })}
          error={errors.min_salary_lpa}
        />
      </div>
    </div>
  );
}
