"use client";

import Link from "next/link";
import { useState, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { Input } from "@/components/ui/field";
import { FormProblem } from "@/components/ui/form-problem";
import { TagList } from "@/components/ui/tag-input";
import { experienceWords } from "@/features/profile/facts";
import { useAction } from "@/lib/useAction";

import {
  check,
  toDraft,
  WORK_MODES,
  type Draft,
  type DraftErrors,
  type PreferenceValues,
} from "./draft";

/** One row of the Settings mock: what it is on the left, the choice on the right. */
function Row({
  title,
  hint,
  error,
  wide = false,
  children,
}: {
  title: string;
  hint: string;
  error?: string;
  /** Chips need the whole width. */
  wide?: boolean;
  children: ReactNode;
}) {
  return (
    <div
      role="group"
      aria-label={title}
      className="flex flex-col gap-2.5 border-t border-rule py-[18px]"
    >
      <div
        className={
          wide ? "flex flex-col gap-2.5" : "flex flex-wrap items-center justify-between gap-4"
        }
      >
        <span className="flex flex-col">
          <span className="font-semibold">{title}</span>
          <span className="text-[13px] text-ink-3">{hint}</span>
        </span>
        <div className="flex flex-wrap items-center gap-2">{children}</div>
      </div>
      <FormProblem>{error ?? null}</FormProblem>
    </div>
  );
}

function Amount({
  label,
  value,
  onChange,
  before,
  after,
  invalid,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  before?: string;
  after: string;
  invalid: boolean;
}) {
  return (
    <span className="flex items-center gap-2">
      {before && <span aria-hidden="true">{before}</span>}
      <Input
        aria-label={label}
        aria-invalid={invalid || undefined}
        inputMode="decimal"
        value={value}
        placeholder="Not set"
        onChange={(event) => onChange(event.target.value)}
        className="h-11 w-[96px]"
      />
      <span>{after}</span>
    </span>
  );
}

/** Settings > Search. One Save for the whole page; the container offers Undo. */
export function SearchSettings({
  saved,
  resumeExperience,
  onSave,
}: {
  saved: PreferenceValues;
  /** Years of experience in the approved profile; undefined when there is no profile. */
  resumeExperience: string | null | undefined;
  onSave: (values: PreferenceValues) => Promise<void>;
}) {
  const [draft, setDraft] = useState<Draft>(() => toDraft(saved));
  const [errors, setErrors] = useState<DraftErrors>({});
  const action = useAction(onSave);
  const changed = JSON.stringify(draft) !== JSON.stringify(toDraft(saved));
  const set = (part: Partial<Draft>) => setDraft((now) => ({ ...now, ...part }));

  return (
    <form
      noValidate
      className="flex flex-col"
      onSubmit={(event) => {
        event.preventDefault();
        const result = check(draft);
        setErrors(result.errors ?? {});
        if (result.values) void action.run(result.values);
      }}
    >
      <Row title="Job titles" hint="What to search for" error={errors.titles} wide>
        <TagList
          items={draft.titles}
          onChange={(titles) => set({ titles })}
          addLabel="Add a title"
        />
      </Row>
      <Row title="Locations" hint="Where you’ll work" error={errors.places} wide>
        <TagList
          items={draft.places}
          onChange={(places) => set({ places })}
          addLabel="Add a place"
        />
      </Row>
      <Row
        title="Work style"
        hint="Choose only some, and other jobs are hidden"
        error={errors.work_modes}
      >
        {WORK_MODES.map((mode) => (
          <Chip
            key={mode.value}
            look="ink"
            pressed={draft.work_modes.includes(mode.value)}
            onPressedChange={(on) =>
              set({
                work_modes: on
                  ? [...draft.work_modes, mode.value]
                  : draft.work_modes.filter((other) => other !== mode.value),
              })
            }
          >
            {mode.label}
          </Chip>
        ))}
      </Row>
      <Row title="Salary" hint="Minimum you’d consider" error={errors.min_salary_lpa}>
        <Amount
          label="Minimum salary in lakhs a year"
          before="₹"
          after="LPA"
          value={draft.min_salary_lpa}
          invalid={Boolean(errors.min_salary_lpa)}
          onChange={(min_salary_lpa) => set({ min_salary_lpa })}
        />
      </Row>
      <Row
        title="Expected pay"
        hint="Used later in application drafts"
        error={errors.expected_ctc_lpa}
      >
        <Amount
          label="Expected pay in lakhs a year"
          before="₹"
          after="LPA"
          value={draft.expected_ctc_lpa}
          invalid={Boolean(errors.expected_ctc_lpa)}
          onChange={(expected_ctc_lpa) => set({ expected_ctc_lpa })}
        />
      </Row>
      <Row title="Experience" hint="From your resume">
        {resumeExperience === undefined ? (
          <Link href="/onboarding" className="text-sm font-semibold">
            Approve your profile first
          </Link>
        ) : (
          <span>{experienceWords(resumeExperience)}</span>
        )}
      </Row>
      <Row
        title="Experience asked by jobs"
        hint="The range you want to see"
        error={errors.experience_min ?? errors.experience_max}
      >
        <Amount
          label="Least years of experience"
          after="to"
          value={draft.experience_min}
          invalid={Boolean(errors.experience_min)}
          onChange={(experience_min) => set({ experience_min })}
        />
        <Amount
          label="Most years of experience"
          after="years"
          value={draft.experience_max}
          invalid={Boolean(errors.experience_max)}
          onChange={(experience_max) => set({ experience_max })}
        />
      </Row>
      <Row title="Notice period" hint="How soon you can join" error={errors.notice_days}>
        <Amount
          label="Notice period in days"
          after="days"
          value={draft.notice_days}
          invalid={Boolean(errors.notice_days)}
          onChange={(notice_days) => set({ notice_days })}
        />
      </Row>
      <Row
        title="Company types to skip"
        hint="Their jobs are hidden"
        error={errors.avoid_company_types}
        wide
      >
        <TagList
          items={draft.avoid_company_types}
          onChange={(avoid_company_types) => set({ avoid_company_types })}
          addLabel="Add a company type"
        />
      </Row>

      <div className="flex flex-col gap-3 border-t-2 border-ink pt-4">
        <FormProblem>{action.problem}</FormProblem>
        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" variant="primary" loading={action.busy} disabled={!changed}>
            Save
          </Button>
          {changed && (
            <Button
              variant="text"
              onClick={() => {
                setDraft(toDraft(saved));
                setErrors({});
                action.clear();
              }}
            >
              Put back
            </Button>
          )}
        </div>
      </div>
    </form>
  );
}
