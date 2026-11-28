/** What the owner types about their search, checked and turned into what the API takes. */
import { z } from "zod";

export type WorkMode = "remote" | "hybrid" | "onsite";

export const WORK_MODES: ReadonlyArray<{ value: WorkMode; label: string }> = [
  { value: "remote", label: "Remote" },
  { value: "hybrid", label: "Hybrid" },
  { value: "onsite", label: "On-site" },
];

/** As the API sends and takes them. Pay is in lakhs a year, written as text. */
export type PreferenceValues = {
  titles: string[];
  places: string[];
  experience_min: number | null;
  experience_max: number | null;
  notice_days: number | null;
  expected_ctc_lpa: string | null;
  min_salary_lpa: string | null;
  work_modes: WorkMode[];
  avoid_company_types: string[];
};

export type Preferences = PreferenceValues & { version: number; onboarding_step: number };

/** The same values while being typed: numbers are text until they are saved. */
export type Draft = {
  titles: string[];
  places: string[];
  experience_min: string;
  experience_max: string;
  notice_days: string;
  expected_ctc_lpa: string;
  min_salary_lpa: string;
  work_modes: WorkMode[];
  avoid_company_types: string[];
};

export function toDraft(values: PreferenceValues): Draft {
  const text = (value: number | string | null) => (value === null ? "" : String(value));
  return {
    titles: values.titles,
    places: values.places,
    experience_min: text(values.experience_min),
    experience_max: text(values.experience_max),
    notice_days: text(values.notice_days),
    expected_ctc_lpa: text(values.expected_ctc_lpa),
    min_salary_lpa: text(values.min_salary_lpa),
    work_modes: values.work_modes,
    avoid_company_types: values.avoid_company_types,
  };
}

const whole = (most: number, message: string) =>
  z
    .string()
    .trim()
    .refine((text) => text === "" || (/^\d+$/.test(text) && Number(text) <= most), message)
    .transform((text) => (text === "" ? null : Number(text)));

const pay = z
  .string()
  .trim()
  .refine(
    (text) =>
      text === "" ||
      (/^\d{1,4}(\.\d{1,2})?$/.test(text) && Number(text) > 0 && Number(text) <= 1000),
    "Enter lakhs a year, such as 14 or 14.5.",
  )
  .transform((text) => (text === "" ? null : text));

const schema = z
  .object({
    titles: z.array(z.string()).max(20, "Keep 20 job titles or fewer."),
    places: z.array(z.string()).max(20, "Keep 20 places or fewer."),
    experience_min: whole(50, "Enter whole years from 0 to 50."),
    experience_max: whole(50, "Enter whole years from 0 to 50."),
    notice_days: whole(365, "Enter whole days from 0 to 365."),
    expected_ctc_lpa: pay,
    min_salary_lpa: pay,
    work_modes: z
      .array(z.enum(["remote", "hybrid", "onsite"]))
      .min(1, "Choose at least one work style."),
    avoid_company_types: z.array(z.string()).max(20, "Keep 20 company types or fewer."),
  })
  .refine(
    (values) =>
      values.experience_min === null ||
      values.experience_max === null ||
      values.experience_min <= values.experience_max,
    { path: ["experience_max"], message: "The most must not be less than the least." },
  );

export type DraftErrors = Partial<Record<keyof Draft, string>>;

export function check(
  draft: Draft,
): { values: PreferenceValues; errors: null } | { values: null; errors: DraftErrors } {
  const result = schema.safeParse(draft);
  if (result.success) return { values: result.data, errors: null };
  const errors: DraftErrors = {};
  for (const issue of result.error.issues) {
    errors[issue.path[0] as keyof Draft] ??= issue.message;
  }
  return { values: null, errors };
}

/** One rupee-lakh up or down, for the phone's − and + buttons. */
export function stepPay(current: string, by: 1 | -1): string {
  const value = Number(current);
  if (current.trim() === "" || !Number.isFinite(value)) return by === 1 ? "1" : "";
  const next = Math.min(1000, Math.round((value + by) * 100) / 100);
  return next > 0 ? String(next) : "";
}
