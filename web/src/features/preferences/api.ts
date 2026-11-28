/** The calls about what the owner is looking for. */
import { api } from "@/lib/api";

import type { Preferences, PreferenceValues } from "./draft";

export const PREFERENCES = ["preferences"];
export const RULES = ["rules"];

export const getPreferences = () => api<Preferences>("/api/preferences");

export const savePreferences = (values: PreferenceValues, version: number) =>
  api<{ preferences: Preferences; event_id: string | null }>("/api/preferences", {
    method: "PUT",
    body: { ...values, version },
  });

/** Notes how far setup got. Nothing depends on it yet, so a failure is not shown. */
export function saveSetupStep(step: number): void {
  void api("/api/preferences/setup-step", { method: "PUT", body: { step } }).catch(() => {});
}

/** Only the values, as they are sent back to be saved. */
export function valuesOf(preferences: Preferences): PreferenceValues {
  return {
    titles: preferences.titles,
    places: preferences.places,
    experience_min: preferences.experience_min,
    experience_max: preferences.experience_max,
    notice_days: preferences.notice_days,
    expected_ctc_lpa: preferences.expected_ctc_lpa,
    min_salary_lpa: preferences.min_salary_lpa,
    work_modes: preferences.work_modes,
    avoid_company_types: preferences.avoid_company_types,
  };
}
