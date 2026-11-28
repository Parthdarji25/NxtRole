/** Grouping facts and comparing a new resume's facts with the approved ones (FR-018). */
import type { Fact, FactKind } from "./types";

/** The order the review list shows them in. */
export const KINDS: ReadonlyArray<{ kind: FactKind; one: string; many: string }> = [
  { kind: "experience_years", one: "Years of experience", many: "Experience" },
  { kind: "role", one: "Role", many: "Roles" },
  { kind: "achievement", one: "Achievement", many: "Achievements" },
  { kind: "skill", one: "Skill", many: "Skills" },
  { kind: "project", one: "Project", many: "Projects" },
  { kind: "education", one: "Education", many: "Education" },
  { kind: "certification", one: "Certification", many: "Certifications" },
  { kind: "location", one: "Location", many: "Location" },
  { kind: "notice_period", one: "Notice period", many: "Notice period" },
];

export function groupFacts(facts: Fact[]) {
  return KINDS.map((group) => ({
    ...group,
    facts: facts.filter((fact) => fact.kind === group.kind),
  })).filter((group) => group.facts.length > 0);
}

/** Skills usually come from one line of the resume, so that line is shown once. */
export function byQuote(facts: Fact[]): Array<{ quote: string | null; facts: Fact[] }> {
  const found = new Map<string | null, Fact[]>();
  for (const fact of facts) {
    const same = found.get(fact.quote);
    if (same) same.push(fact);
    else found.set(fact.quote, [fact]);
  }
  return [...found].map(([quote, grouped]) => ({ quote, facts: grouped }));
}

const plain = (text: string | null) => (text ?? "").toLowerCase().replace(/\s+/g, " ").trim();

/** Two facts with the same key are about the same thing. */
const keyOf = (fact: Fact) => [fact.kind, plain(fact.value), plain(fact.company)].join("|");

export type Comparison = {
  /** Compared with the approved facts. A fact with no entry has not changed. */
  marks: Record<string, "new" | "changed">;
  /** Approved facts the new resume does not mention. */
  missing: Fact[];
  /** What the owner starts reviewing: the new facts, plus those they wrote themselves. */
  start: Fact[];
};

export function compare(suggested: Fact[], approved: Fact[] | null): Comparison {
  if (!approved) return { marks: {}, missing: [], start: suggested };
  const before = new Map(approved.map((fact) => [keyOf(fact), fact]));
  const after = new Set(suggested.map(keyOf));
  const marks: Comparison["marks"] = {};
  for (const fact of suggested) {
    const old = before.get(keyOf(fact));
    if (!old) marks[fact.fact_id] = "new";
    else if (plain(old.dates) !== plain(fact.dates)) marks[fact.fact_id] = "changed";
  }
  const absent = approved.filter((fact) => !after.has(keyOf(fact)));
  // A new resume cannot mention what the owner added by hand, so that is kept.
  const own = withFreshIds(
    absent.filter((fact) => fact.source === "you"),
    suggested,
  );
  return {
    marks,
    missing: absent.filter((fact) => fact.source === "resume"),
    start: [...suggested, ...own],
  };
}

export function newFactId(): string {
  return `you-${crypto.randomUUID().slice(0, 8)}`;
}

/** Gives facts new ids where theirs is already used. */
export function withFreshIds(facts: Fact[], taken: Fact[]): Fact[] {
  const used = new Set(taken.map((fact) => fact.fact_id));
  return facts.map((fact) => {
    const kept = used.has(fact.fact_id) ? { ...fact, fact_id: newFactId() } : fact;
    used.add(kept.fact_id);
    return kept;
  });
}

/** "4" is shown as "4 years"; anything else as it is written. */
export function experienceWords(value: string | null): string {
  if (!value) return "Not stated";
  if (!/^\d+(\.\d+)?$/.test(value)) return value;
  return value === "1" ? "1 year" : `${value} years`;
}
