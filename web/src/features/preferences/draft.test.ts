import { describe, expect, it } from "vitest";

import type { Fact } from "@/features/profile/types";

import { check, stepPay, toDraft, type Draft, type PreferenceValues } from "./draft";
import { suggestionsFrom } from "./suggestions";

const NOTHING: PreferenceValues = {
  titles: [],
  places: [],
  experience_min: null,
  experience_max: null,
  notice_days: null,
  expected_ctc_lpa: null,
  min_salary_lpa: null,
  work_modes: ["remote", "hybrid", "onsite"],
  avoid_company_types: [],
};

const typed = (part: Partial<Draft>) => check({ ...toDraft(NOTHING), ...part });

describe("checking what was typed", () => {
  it("turns empty boxes into nothing and keeps the numbers", () => {
    expect(typed({}).values).toEqual(NOTHING);
    expect(
      typed({ min_salary_lpa: " 14.5 ", notice_days: "0", experience_max: "5" }).values,
    ).toMatchObject({ min_salary_lpa: "14.5", notice_days: 0, experience_max: 5 });
  });

  it.each<[Partial<Draft>, keyof Draft]>([
    [{ min_salary_lpa: "0" }, "min_salary_lpa"],
    [{ min_salary_lpa: "-3" }, "min_salary_lpa"],
    [{ min_salary_lpa: "14.123" }, "min_salary_lpa"],
    [{ min_salary_lpa: "1001" }, "min_salary_lpa"],
    [{ expected_ctc_lpa: "lots" }, "expected_ctc_lpa"],
    [{ notice_days: "400" }, "notice_days"],
    [{ notice_days: "1.5" }, "notice_days"],
    [{ experience_min: "5", experience_max: "2" }, "experience_max"],
    [{ work_modes: [] }, "work_modes"],
    [{ titles: Array.from({ length: 21 }, (_, n) => `Title ${n}`) }, "titles"],
  ])("refuses %o and says where", (part, field) => {
    const result = typed(part);

    expect(result.values).toBeNull();
    expect(result.errors?.[field]).toBeTruthy();
  });

  it.each([
    ["14", 1, "15"],
    ["14.5", -1, "13.5"],
    ["1", -1, ""],
    ["", 1, "1"],
    ["", -1, ""],
    ["1000", 1, "1000"],
  ] as const)("the phone button turns %s by %i into %s", (from, by, to) => {
    expect(stepPay(from, by)).toBe(to);
  });
});

describe("suggestions for step 2", () => {
  const fact = (kind: Fact["kind"], value: string): Fact => ({
    fact_id: value,
    kind,
    value,
    company: null,
    dates: null,
    quote: null,
    source: "you",
  });

  it("come only from approved facts", () => {
    expect(suggestionsFrom(null, null)).toEqual({ titles: [], places: [] });
  });

  it("offer the current role first, the city, and remote work", () => {
    const facts = [
      fact("role", "Junior Developer"),
      fact("role", "Frontend Developer"),
      fact("location", "Pune, Maharashtra"),
    ];

    expect(suggestionsFrom(facts, "Frontend Developer")).toEqual({
      titles: ["Frontend Developer", "Junior Developer"],
      places: ["Pune", "Remote (India)"],
    });
  });
});
