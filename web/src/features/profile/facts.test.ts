import { describe, expect, it } from "vitest";

import { byQuote, compare, experienceWords, groupFacts, withFreshIds } from "./facts";
import { MAX_BYTES, problemWith } from "./resumeFile";
import type { Fact, FactKind } from "./types";

function fact(id: string, kind: FactKind, value: string, more: Partial<Fact> = {}): Fact {
  return {
    fact_id: id,
    kind,
    value,
    company: null,
    dates: null,
    quote: value,
    source: "resume",
    ...more,
  };
}

describe("comparing a new resume with the approved facts (FR-018)", () => {
  const approved = [
    fact("a1", "role", "Developer", { company: "One Ltd", dates: "2021 - 2023" }),
    fact("a2", "skill", "React"),
    fact("a3", "skill", "jQuery"),
    fact("a4", "notice_period", "30 days", { source: "you", quote: null }),
  ];
  const suggested = [
    fact("f1", "role", "developer", { company: "One  Ltd", dates: "2021 - 2024" }),
    fact("f2", "skill", "React"),
    fact("f3", "skill", "Playwright"),
  ];

  it("marks what is new or changed, ignoring capitals and spacing", () => {
    expect(compare(suggested, approved).marks).toEqual({ f1: "changed", f3: "new" });
  });

  it("lists resume facts that are gone, and keeps what the owner wrote", () => {
    const result = compare(suggested, approved);

    expect(result.missing.map((item) => item.value)).toEqual(["jQuery"]);
    expect(result.start.map((item) => item.value)).toEqual([
      "developer",
      "React",
      "Playwright",
      "30 days",
    ]);
  });

  it("marks nothing on the first resume", () => {
    expect(compare(suggested, null)).toEqual({ marks: {}, missing: [], start: suggested });
  });

  it("never gives two facts the same id", () => {
    const [kept] = withFreshIds([fact("f1", "skill", "Git")], suggested);

    expect(kept!.fact_id).not.toBe("f1");
    const own = [fact("f1", "notice_period", "15 days", { source: "you" })];
    const ids = compare(suggested, own).start.map((item) => item.fact_id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});

describe("showing facts", () => {
  it("groups them in a fixed order and shows one skills line once", () => {
    const facts = [
      fact("s1", "skill", "React", { quote: "Skills: React, Git" }),
      fact("r1", "role", "Developer"),
      fact("s2", "skill", "Git", { quote: "Skills: React, Git" }),
    ];

    expect(groupFacts(facts).map((group) => group.kind)).toEqual(["role", "skill"]);
    expect(byQuote(groupFacts(facts)[1]!.facts)).toHaveLength(1);
  });

  it.each([
    ["4", "4 years"],
    ["1", "1 year"],
    ["2.5", "2.5 years"],
    ["about 4 years", "about 4 years"],
    [null, "Not stated"],
  ])("writes experience %s as %s", (value, words) => {
    expect(experienceWords(value)).toBe(words);
  });
});

describe("checking a file before it is sent", () => {
  it.each([
    ["resume.pdf", 100, null],
    ["Resume.DOCX", MAX_BYTES, null],
    ["resume.doc", 100, "Upload a PDF or a Word (.docx) file."],
    ["photo.png", 100, "Upload a PDF or a Word (.docx) file."],
    ["resume.pdf", 0, "That file is empty."],
    ["resume.pdf", MAX_BYTES + 1, "That file is over 5 MB."],
  ])("%s of %i bytes", (name, size, problem) => {
    expect(problemWith({ name, size })).toBe(problem);
  });
});
