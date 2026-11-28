"use client";

import { Banner, ErrorState, ListSkeleton } from "@/components/states/states";
import { Button } from "@/components/ui/button";

import { FactReview } from "./FactReview";
import { IdentityCheck } from "./IdentityCheck";
import { ProfileSummary } from "./ProfileSummary";
import { ResumeCard } from "./ResumeCard";
import { ResumeDropZone } from "./ResumeDropZone";
import type { Detected, Fact, FileWarning, Identity, ResumeFile, Summary, Version } from "./types";

type Shown = Pick<ResumeFile, "name" | "content_type">;

/** Everything Onboarding step 1 can be showing. */
export type ResumeState =
  | { status: "loading" }
  | { status: "error"; message: string; retry: () => void }
  | { status: "choose"; problem?: string | null; onFile: (file: File) => void }
  | { status: "sending"; file: Shown; stage: "uploading" | "checking" }
  | {
      status: "identity";
      file: Shown;
      detected: Detected;
      saved: Identity | null;
      warnings: FileWarning[];
      duplicate: boolean;
      onConfirm: (identity: Identity) => Promise<void>;
      onReplace: () => void;
    }
  | { status: "reading"; file: Shown }
  /** Waiting for the free AI limit, or failed. */
  | {
      status: "stopped";
      file: Shown;
      waiting: boolean;
      message: string;
      onRetry: () => void;
      onReplace: () => void;
    }
  | {
      status: "review";
      file: Shown;
      facts: Fact[];
      approved: Fact[] | null;
      dropped: number;
      onApprove: (facts: Fact[]) => Promise<void>;
      onDiscard: () => Promise<void>;
      onReplace: () => void;
    }
  | {
      status: "approved";
      file: Shown | null;
      summary: Summary;
      version: Version;
      approvedOn: string;
      onEdit: () => void;
      onReplace: () => void;
    }
  | {
      status: "editing";
      facts: Fact[];
      onSave: (facts: Fact[]) => Promise<void>;
      onCancel: () => void;
    };

const WARNINGS: Record<FileWarning, string> = {
  truncated: "This resume is long. Only the first part of it will be read.",
  not_english: "This resume does not look like English, so some facts may be missed.",
};

export function ResumeStep({
  state,
  aiNotReady = null,
}: {
  state: ResumeState;
  /** Why AI cannot read a resume yet, if it cannot. */
  aiNotReady?: string | null;
}) {
  if (state.status === "loading") return <ListSkeleton rows={2} label="Loading your profile" />;
  if (state.status === "error") {
    return <ErrorState onRetry={state.retry}>{state.message}</ErrorState>;
  }

  return (
    <div className="flex flex-col gap-4 md:gap-[22px]">
      {aiNotReady && state.status !== "approved" && state.status !== "editing" && (
        <Banner tag="AI not ready">{aiNotReady}</Banner>
      )}

      {state.status === "choose" && (
        <ResumeDropZone onFile={state.onFile} problem={state.problem} />
      )}

      {state.status === "sending" && (
        <ResumeCard
          file={state.file}
          status={state.stage === "uploading" ? "Uploading…" : "Reading text…"}
          progress={state.stage === "uploading" ? 30 : 60}
        />
      )}

      {state.status === "identity" && (
        <>
          <ResumeCard
            file={state.file}
            status="Text read · nothing sent to AI yet"
            progress={60}
            onReplace={state.onReplace}
          />
          {state.duplicate && (
            <Banner tone="blue" tag="Seen before">
              You uploaded this file earlier, so the saved copy is used.
            </Banner>
          )}
          {state.warnings.map((warning) => (
            <Banner key={warning} tag="Note">
              {WARNINGS[warning]}
            </Banner>
          ))}
          <IdentityCheck
            detected={state.detected}
            saved={state.saved}
            onConfirm={state.onConfirm}
          />
        </>
      )}

      {state.status === "reading" && (
        <ResumeCard file={state.file} status="Finding skills with AI…" progress={80}>
          <p className="text-[13px] text-ink-3">
            This can take a minute on the free plan. You can leave this page; nothing is lost.
          </p>
        </ResumeCard>
      )}

      {state.status === "stopped" && (
        <ResumeCard
          file={state.file}
          status={state.waiting ? "Waiting for AI" : "Not read"}
          progress={60}
          onReplace={state.onReplace}
        >
          <Banner
            tone={state.waiting ? "amber" : "red"}
            tag={state.waiting ? "Waiting" : "Stopped"}
            action={
              <Button size="sm" onClick={state.onRetry}>
                Try again
              </Button>
            }
          >
            {state.message}
          </Banner>
        </ResumeCard>
      )}

      {state.status === "review" && (
        <>
          <ResumeCard
            file={state.file}
            status="Read · identity removed · waiting for your approval"
            progress={90}
            onReplace={state.onReplace}
          />
          <FactReview
            // A different suggestion starts a fresh review.
            key={state.facts.map((fact) => fact.fact_id).join()}
            mode="suggestion"
            facts={state.facts}
            approved={state.approved}
            dropped={state.dropped}
            onSave={state.onApprove}
            onCancel={state.onDiscard}
          />
        </>
      )}

      {state.status === "approved" && (
        <>
          {state.file ? (
            <ResumeCard
              file={state.file}
              status="Read · identity removed · approved"
              progress={100}
              onReplace={state.onReplace}
            >
              <ProfileSummary
                summary={state.summary}
                versionNo={state.version.version_no}
                approvedOn={state.approvedOn}
                onEdit={state.onEdit}
              />
            </ResumeCard>
          ) : (
            <>
              <ProfileSummary
                summary={state.summary}
                versionNo={state.version.version_no}
                approvedOn={state.approvedOn}
                onEdit={state.onEdit}
              />
              <Button className="self-start" onClick={state.onReplace}>
                Upload a new resume
              </Button>
            </>
          )}
        </>
      )}

      {state.status === "editing" && (
        <FactReview
          mode="edit"
          facts={state.facts}
          onSave={state.onSave}
          onCancel={state.onCancel}
        />
      )}
    </div>
  );
}
