import Link from "next/link";

import { ErrorState, ListSkeleton } from "@/components/states/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export type Rule = {
  id: string;
  kind: string;
  text: string;
  origin: string;
  status: string;
  hid_count: number;
};

export type RuleList =
  | { status: "loading" }
  | { status: "error"; message: string; retry: () => void }
  | { status: "ready"; items: Rule[] };

const SEARCH_SETTINGS = "/settings?section=search";

function effect(rule: Rule): string {
  if (rule.hid_count === 0) return "Applies when job search starts";
  return `Hid ${rule.hid_count} ${rule.hid_count === 1 ? "job" : "jobs"}`;
}

/** "Your rules" on Sources and memory. Editing them here arrives in Phase 7. */
export function RulesList({ rules }: { rules: RuleList }) {
  return (
    <section aria-labelledby="rules-title" className="flex flex-col">
      <h2 id="rules-title" className="heading pb-2.5 text-[26px]">
        Your rules
      </h2>
      {rules.status === "loading" && <ListSkeleton rows={2} label="Loading your rules" />}
      {rules.status === "error" && <ErrorState onRetry={rules.retry}>{rules.message}</ErrorState>}
      {rules.status === "ready" &&
        (rules.items.length === 0 ? (
          <div className="flex flex-col items-start gap-3 border-y border-rule py-5">
            <p className="text-ink-2">
              No rules yet. A minimum salary, a work style or a company type to skip becomes a rule.
            </p>
            <Button asChild>
              <Link href={SEARCH_SETTINGS}>Set them in Search</Link>
            </Button>
          </div>
        ) : (
          <ul>
            {rules.items.map((rule) => (
              <li
                key={rule.id}
                className="flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-rule py-3.5 last:border-b"
              >
                <span className="flex min-w-0 flex-[1_1_280px] flex-col">
                  <span className="font-semibold break-words">{rule.text}</span>
                  <span className="text-[13px] text-ink-3">{effect(rule)}</span>
                </span>
                <Badge>{rule.origin === "you" ? "You set" : "Learned"}</Badge>
                <Button asChild variant="text" size="sm">
                  <Link href={SEARCH_SETTINGS} aria-label={`Change: ${rule.text}`}>
                    Change
                  </Link>
                </Button>
              </li>
            ))}
          </ul>
        ))}
    </section>
  );
}
