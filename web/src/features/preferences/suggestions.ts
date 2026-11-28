/** What step 2 offers, taken only from approved facts. */
import type { Fact } from "@/features/profile/types";

const MOST_TITLES = 4;
export const REMOTE = "Remote (India)";

const unique = (values: string[]) => [
  ...new Map(values.map((value) => [value.toLowerCase(), value])).values(),
];

const fits = (value: string) => value.length >= 2 && value.length <= 80;

/** Titles from the roles, the current one first; places from the locations. */
export function suggestionsFrom(facts: Fact[] | null, latestRole: string | null) {
  if (!facts) return { titles: [], places: [] };
  const roles = facts.filter((fact) => fact.kind === "role").map((fact) => fact.value);
  const titles = unique([...(latestRole ? [latestRole] : []), ...roles])
    // A longer line is not a job title the API would take.
    .filter(fits)
    .slice(0, MOST_TITLES);
  const places = unique(
    facts
      .filter((fact) => fact.kind === "location")
      // "Pune, Maharashtra" is the city Pune.
      .map((fact) => fact.value.split(",")[0]!.trim())
      .filter(fits),
  );
  return { titles, places: unique([...places, REMOTE]) };
}
