import { Button } from "@/components/ui/button";
import { Kicker } from "@/components/ui/layout";

import { experienceWords } from "./facts";
import type { Summary } from "./types";

/** The green box names only the first few skills; "Review or edit facts" shows them all. */
const PHONE_SKILLS = 4;

function Part({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex min-w-0 flex-col gap-1">
      <Kicker>{label}</Kicker>
      <span className="heading text-[22px] break-words md:text-[28px]">{value}</span>
    </div>
  );
}

/** What the approved profile says, as Onboarding step 1 shows it. */
export function ProfileSummary({
  summary,
  versionNo,
  approvedOn,
  onEdit,
}: {
  summary: Summary;
  versionNo: number;
  /** Already formatted, for example "28 Nov 2026". */
  approvedOn: string;
  onEdit: () => void;
}) {
  return (
    <div className="flex flex-col gap-4">
      {/* The phone mock sums it up in one green box. */}
      <div className="flex flex-col gap-2 rounded-xl bg-green-soft p-3.5 md:hidden">
        <span className="font-semibold text-green">Found in your resume</span>
        <span className="text-sm break-words">
          {[
            summary.experience_years && experienceWords(summary.experience_years),
            summary.skills.slice(0, PHONE_SKILLS).join(", "),
            summary.latest_role,
          ]
            .filter(Boolean)
            .join(" · ")}
        </span>
      </div>
      <div className="grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] gap-[18px] max-md:hidden">
        <Part label="Experience" value={experienceWords(summary.experience_years)} />
        <Part label="Latest role" value={summary.latest_role ?? "Not stated"} />
        <div className="col-span-full flex flex-col gap-2">
          <Kicker>Skills found · {summary.skills.length}</Kicker>
          <ul className="flex flex-wrap gap-1.5">
            {summary.skills.map((skill) => (
              <li
                key={skill}
                className="rounded-md border border-rule-2 px-2.5 py-0.5 text-[13px] break-all"
              >
                {skill}
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-rule pt-3">
        <span className="text-[13px] text-ink-3">
          Profile version {versionNo} · approved {approvedOn}
        </span>
        <Button size="sm" onClick={onEdit}>
          Review or edit facts
        </Button>
      </div>
    </div>
  );
}
