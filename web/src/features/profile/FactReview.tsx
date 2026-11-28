"use client";

import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FormProblem } from "@/components/ui/form-problem";
import { Kicker } from "@/components/ui/layout";
import { cn } from "@/lib/cn";
import { useAction } from "@/lib/useAction";

import { FactForm } from "./FactForm";
import { byQuote, compare, experienceWords, groupFacts, withFreshIds } from "./facts";
import type { Fact } from "./types";

type Mark = "new" | "changed" | undefined;

function Tags({ fact, mark }: { fact: Fact; mark: Mark }) {
  return (
    <>
      {mark === "new" && <Badge tone="blue">New</Badge>}
      {mark === "changed" && <Badge tone="amber">Changed</Badge>}
      {fact.source === "you" && <Badge>Written by you</Badge>}
    </>
  );
}

function Quote({ children }: { children: string }) {
  return (
    <p className="border-l-2 border-rule-2 pl-2.5 text-[13px] break-words text-ink-3">
      From your resume: <q>{children}</q>
    </p>
  );
}

/**
 * Every fact with the words it came from. The owner edits, removes or adds, then approves;
 * until then nothing is saved (golden rule 2).
 */
export function FactReview({
  facts: suggested,
  approved = null,
  dropped = 0,
  mode,
  onSave,
  onCancel,
}: {
  facts: Fact[];
  /** The facts in use now, to show what a new resume would change. */
  approved?: Fact[] | null;
  /** Suggestions left out because the resume does not state them. */
  dropped?: number;
  /** "suggestion": approving what AI read. "edit": changing the approved facts. */
  mode: "suggestion" | "edit";
  onSave: (facts: Fact[]) => Promise<void>;
  /** "Discard" for a suggestion, "Cancel" for an edit. */
  onCancel: () => Promise<void> | void;
}) {
  const comparison = useMemo(() => compare(suggested, approved), [suggested, approved]);
  const [facts, setFacts] = useState(comparison.start);
  const [removed, setRemoved] = useState<ReadonlySet<string>>(new Set());
  const [editing, setEditing] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const save = useAction(onSave);
  const cancel = useAction(async () => onCancel());

  const kept = facts.filter((fact) => !removed.has(fact.fact_id));
  const groups = groupFacts(facts);
  const stillMissing = comparison.missing.filter(
    (old) => !facts.some((fact) => fact.kind === old.kind && fact.value === old.value),
  );

  function replace(next: Fact) {
    setFacts((now) => now.map((fact) => (fact.fact_id === next.fact_id ? next : fact)));
    setEditing(null);
  }

  function toggle(id: string) {
    setRemoved((now) => {
      const next = new Set(now);
      if (!next.delete(id)) next.add(id);
      return next;
    });
  }

  function row(fact: Fact, showQuote: boolean) {
    if (editing === fact.fact_id) {
      return <FactForm fact={fact} onSave={replace} onCancel={() => setEditing(null)} />;
    }
    const gone = removed.has(fact.fact_id);
    return (
      <div className="flex flex-wrap items-start gap-x-4 gap-y-1">
        <div className="flex min-w-0 flex-[1_1_280px] flex-col gap-1">
          <span className="flex flex-wrap items-center gap-2">
            <span className={cn("font-semibold break-words", gone && "text-ink-3 line-through")}>
              {fact.kind === "experience_years" ? experienceWords(fact.value) : fact.value}
            </span>
            {gone ? <Badge tone="red">Removed</Badge> : <Tags fact={fact} mark={mark(fact)} />}
          </span>
          {!gone && (fact.company || fact.dates) && (
            <span className="text-sm text-ink-2">
              {[fact.company, fact.dates].filter(Boolean).join(" · ")}
            </span>
          )}
          {!gone && showQuote && fact.quote && <Quote>{fact.quote}</Quote>}
        </div>
        <span className="flex gap-1">
          {gone ? (
            <Button
              variant="text"
              size="sm"
              onClick={() => toggle(fact.fact_id)}
              aria-label={`Put back: ${fact.value}`}
            >
              Put back
            </Button>
          ) : (
            <>
              <Button
                variant="text"
                size="sm"
                onClick={() => setEditing(fact.fact_id)}
                aria-label={`Edit: ${fact.value}`}
              >
                Edit
              </Button>
              <Button
                variant="text"
                size="sm"
                onClick={() => toggle(fact.fact_id)}
                aria-label={`Remove: ${fact.value}`}
              >
                Remove
              </Button>
            </>
          )}
        </span>
      </div>
    );
  }

  const mark = (fact: Fact): Mark => comparison.marks[fact.fact_id];

  /** Skills as chips under the line they came from. */
  function chips(list: Fact[]) {
    return byQuote(list).map((group) => (
      <div key={group.quote ?? "yours"} className="flex flex-col gap-2 border-t border-rule py-3.5">
        <ul className="flex flex-wrap gap-2">
          {group.facts.map((fact) => {
            const gone = removed.has(fact.fact_id);
            return (
              <li
                key={fact.fact_id}
                className="inline-flex min-h-9 items-center gap-1.5 rounded-md border border-rule-2 py-1 pr-1 pl-3 text-sm"
              >
                <span className={cn("break-all", gone && "text-ink-3 line-through")}>
                  {fact.value}
                </span>
                {!gone && <Tags fact={fact} mark={mark(fact)} />}
                <button
                  type="button"
                  onClick={() => toggle(fact.fact_id)}
                  aria-label={gone ? `Put back ${fact.value}` : `Remove ${fact.value}`}
                  className="hit-target size-7 shrink-0 text-ink-3 hover:text-ink"
                >
                  <span aria-hidden="true">{gone ? "↺" : "✕"}</span>
                </button>
              </li>
            );
          })}
        </ul>
        {group.quote && <Quote>{group.quote}</Quote>}
      </div>
    ));
  }

  return (
    <section aria-labelledby="review-title" className="flex flex-col gap-5">
      <div className="flex flex-col gap-1.5">
        <h2 id="review-title" className="heading text-[26px]">
          {mode === "edit" ? "Your approved facts" : "Check what was found"}
        </h2>
        <p className="max-w-[600px] text-ink-2">
          {mode === "edit"
            ? "Change, remove or add anything. Saving makes a new version, and you can undo it."
            : "Each fact shows the words it came from. Fix anything that is wrong. Nothing is saved until you approve."}
        </p>
        {dropped > 0 && (
          <p className="text-[13px] text-ink-3">
            {dropped === 1
              ? "1 suggestion was left out because your resume does not say it."
              : `${dropped} suggestions were left out because your resume does not say them.`}
          </p>
        )}
      </div>

      {groups.map((group) => (
        <section key={group.kind} aria-label={group.many} className="flex flex-col">
          <h3 className="pb-2">
            <Kicker>
              {group.many} · {group.facts.filter((fact) => !removed.has(fact.fact_id)).length}
            </Kicker>
          </h3>
          {group.kind === "skill" ? (
            chips(group.facts)
          ) : (
            <ul>
              {group.facts.map((fact) => (
                <li key={fact.fact_id} className="border-t border-rule py-3.5">
                  {row(fact, true)}
                </li>
              ))}
            </ul>
          )}
        </section>
      ))}

      {stillMissing.length > 0 && (
        <section aria-label="Not in the new resume" className="flex flex-col">
          <h3 className="pb-1">
            <Kicker>Not in the new resume · {stillMissing.length}</Kicker>
          </h3>
          <p className="pb-2 text-[13px] text-ink-3">
            These leave your profile when you approve, unless you keep them.
          </p>
          <ul>
            {stillMissing.map((old) => (
              <li
                key={old.fact_id}
                className="flex flex-wrap items-center justify-between gap-3 border-t border-rule py-3"
              >
                <span className="flex min-w-0 flex-col">
                  <span className="break-words text-ink-2">{old.value}</span>
                  {(old.company || old.dates) && (
                    <span className="text-[13px] text-ink-3">
                      {[old.company, old.dates].filter(Boolean).join(" · ")}
                    </span>
                  )}
                </span>
                <Button
                  size="sm"
                  onClick={() => setFacts((now) => [...now, ...withFreshIds([old], now)])}
                  aria-label={`Keep: ${old.value}`}
                >
                  Keep
                </Button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {adding ? (
        <FactForm
          onSave={(fact) => {
            setFacts((now) => [...now, fact]);
            setAdding(false);
          }}
          onCancel={() => setAdding(false)}
        />
      ) : (
        <Button className="self-start" onClick={() => setAdding(true)}>
          Add a fact
        </Button>
      )}

      <FormProblem>{save.problem ?? cancel.problem}</FormProblem>
      {(editing !== null || adding) && (
        <p className="-mb-2 text-[13px] text-ink-3">
          Keep or cancel the open change before {mode === "edit" ? "saving" : "approving"}.
        </p>
      )}
      <div className="flex flex-wrap items-center gap-3 border-t-2 border-ink pt-4">
        <Button
          variant="primary"
          size="lg"
          loading={save.busy}
          disabled={kept.length === 0 || editing !== null || adding}
          onClick={() => save.run(kept)}
        >
          {mode === "edit"
            ? "Save changes"
            : `Approve ${kept.length} ${kept.length === 1 ? "fact" : "facts"}`}
        </Button>
        <Button variant="text" loading={cancel.busy} onClick={() => cancel.run()}>
          {mode === "edit" ? "Cancel" : "Discard these suggestions"}
        </Button>
      </div>
    </section>
  );
}
