import type { ReactNode } from "react";

import { Banner } from "@/components/states/states";
import { Kicker } from "@/components/ui/layout";
import { cn } from "@/lib/cn";

function Row({ title, hint, children }: { title: string; hint: string; children?: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4 border-t border-rule py-[18px]">
      <span className="flex flex-1 flex-col">
        <span className="font-semibold">{title}</span>
        <span className="text-[13px] text-ink-3">{hint}</span>
      </span>
      {children}
    </div>
  );
}

function Status({ good, children }: { good: boolean; children: ReactNode }) {
  return (
    <span className={cn("text-right text-sm font-semibold", good ? "text-green" : "text-amber")}>
      {children}
    </span>
  );
}

/**
 * Settings > Privacy (FR-199): what protects the owner and what is stored. Nothing here is a
 * switch: hiding identity cannot be turned off.
 */
export function PrivacySettings({
  confirmedOn,
}: {
  /** The date the owner confirmed Zero Data Retention, already formatted; null if not. */
  confirmedOn: string | null;
}) {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col">
        <Row
          title="Hide my identity from AI"
          hint="Name, phone, email, links and address are removed before AI reads anything"
        >
          <Status good>Always on</Status>
        </Row>
        <Row
          title="Zero data retention"
          hint="A setting in Groq’s console that stops Groq keeping prompts and replies. NxtRole records your confirmation; it cannot check Groq."
        >
          <Status good={confirmedOn !== null}>
            {confirmedOn ? `Confirmed ${confirmedOn}` : "Not confirmed"}
          </Status>
        </Row>
        {!confirmedOn && (
          <Banner tag="AI paused">
            AI will not read your resume until you switch it on in Groq’s console and add the date
            to GROQ_ZDR_CONFIRMED_ON in api/.env.
          </Banner>
        )}
        <Row
          title="What AI reads"
          hint="The words of your resume with those details removed, sent to Groq (servers in the United States)"
        />
        <Row
          title="Never sent to AI"
          hint="Email addresses, phone numbers, ID numbers, and lines such as date of birth or parents’ names"
        />
      </div>

      <div className="flex flex-col">
        <h3 className="pb-2">
          <Kicker>What is stored</Kicker>
        </h3>
        <Row
          title="Resume files and their text"
          hint="Private storage that only your sign-in can reach. Export and delete arrive in a later update."
        />
        <Row title="Profile versions" hint="Every version you approved, so that you can go back" />
        <Row title="AI usage" hint="Counts of requests and tokens per model. Never the text." />
      </div>
    </div>
  );
}
