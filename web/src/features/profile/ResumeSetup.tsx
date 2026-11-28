"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { showToast } from "@/components/ui/toast";
import { OnboardingFrame } from "@/features/onboarding/OnboardingFrame";
import { ResumeHeading } from "@/features/onboarding/ResumeHeading";
import { saveSetupStep } from "@/features/preferences/api";
import { api, ApiError } from "@/lib/api";
import { mediumDate } from "@/lib/dates";
import { offerUndo } from "@/lib/undo";
import { reasonFor } from "@/lib/useAction";

import {
  getFile,
  getPrivacy,
  getProfile,
  PRIVACY,
  PROFILE,
  retryReading,
  startReading,
  uploadResume,
  type CheckedFile,
  type PrivacyInfo,
} from "./api";
import { contentTypeOf, PDF } from "./resumeFile";
import { ResumeStep, type ResumeState } from "./ResumeStep";
import type { Fact, Reading, ResumeFile } from "./types";

/** How often to ask whether the resume has been read. */
export const CHECK_EVERY_MILLISECONDS = 2_000;

type Shown = Pick<ResumeFile, "name" | "content_type">;

/** What the owner is in the middle of here. Everything else comes from the API. */
type Local =
  | { kind: "none" }
  | { kind: "choosing"; problem: string | null }
  | { kind: "sending"; file: Shown; stage: "uploading" | "checking" }
  | { kind: "identity"; checked: CheckedFile }
  | { kind: "editing" };

const NOT_READY: Partial<Record<PrivacyInfo["status"], string>> = {
  not_set_up:
    "AI is not set up: the Groq key is missing. You can upload now and have it read once the key is added.",
  privacy_not_confirmed:
    "AI will not read your resume until Zero Data Retention is confirmed (see Settings, Privacy).",
};

const inProgress = (reading: Reading) =>
  reading.state === "running" || (reading.state === "queued" && !reading.code);

/** Waiting for the free limit, or failed. A replaced attempt is of no interest. */
const hasStopped = (reading: Reading) =>
  (reading.state === "failed" && reading.code !== "replaced") ||
  (reading.state === "queued" && Boolean(reading.code));

const UNNAMED: Shown = { name: "Your resume", content_type: PDF };

/** Onboarding step 1, connected to the API. */
export function ResumeSetup() {
  const router = useRouter();
  const queries = useQueryClient();
  const [local, setLocal] = useState<Local>({ kind: "none" });
  // A stopped attempt the owner has put aside.
  const [dismissed, setDismissed] = useState<string | null>(null);

  const profile = useQuery({
    queryKey: PROFILE,
    queryFn: getProfile,
    refetchInterval: (query) => {
      const latest = query.state.data?.reading;
      return latest && inProgress(latest) ? CHECK_EVERY_MILLISECONDS : false;
    },
  });
  const privacy = useQuery({ queryKey: PRIVACY, queryFn: getPrivacy });
  const data = profile.data;
  const reading = data?.reading ?? null;
  const reads = reading && inProgress(reading) ? reading : null;
  const stopped = reading && hasStopped(reading) && reading.job_id !== dismissed ? reading : null;
  const fileId =
    (reads ?? stopped)?.file_id ??
    data?.suggestion?.source_file_id ??
    data?.approved?.source_file_id ??
    null;
  const stored = useQuery({
    queryKey: ["file", fileId],
    queryFn: () => getFile(fileId!),
    enabled: fileId !== null,
  });
  const file: Shown = stored.data ?? UNNAMED;

  const refresh = () => queries.invalidateQueries({ queryKey: PROFILE });
  const choose = (problem: string | null = null) => setLocal({ kind: "choosing", problem });
  const rest = () => setLocal({ kind: "none" });

  async function upload(chosen: File) {
    const shown = { name: chosen.name, content_type: contentTypeOf(chosen.name) ?? chosen.type };
    setLocal({ kind: "sending", file: shown, stage: "uploading" });
    try {
      const checked = await uploadResume(chosen, () =>
        setLocal({ kind: "sending", file: shown, stage: "checking" }),
      );
      setLocal({ kind: "identity", checked });
    } catch (error) {
      choose(reasonFor(error));
    }
  }

  /** Runs a decision. If it was already made elsewhere, shows what is stored now. */
  async function decide<Result>(task: () => Promise<Result>): Promise<Result> {
    try {
      return await task();
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) await refresh();
      throw error;
    }
  }

  function state(): ResumeState {
    if (!data) {
      return profile.isError
        ? {
            status: "error",
            message: reasonFor(profile.error),
            retry: () => void profile.refetch(),
          }
        : { status: "loading" };
    }
    const { approved, suggestion, summary } = data;

    if (local.kind === "choosing") {
      const back = approved || suggestion ? rest : undefined;
      return { status: "choose", problem: local.problem, onFile: upload, onBack: back };
    }
    if (local.kind === "sending") {
      return { status: "sending", file: local.file, stage: local.stage };
    }
    if (local.kind === "identity") {
      const { checked } = local;
      return {
        status: "identity",
        file: checked.file,
        detected: checked.detected,
        saved: checked.file.hidden_identity,
        warnings: checked.warnings,
        duplicate: checked.duplicate,
        onReplace: () => choose(),
        onConfirm: async (identity) => {
          await startReading(checked.file.id, identity);
          setDismissed(null);
          await refresh();
          rest();
        },
      };
    }
    if (local.kind === "editing" && approved) {
      return {
        status: "editing",
        facts: approved.facts,
        onCancel: rest,
        onSave: async (facts: Fact[]) => {
          const saved = await decide(() =>
            api<{ event_id: string | null }>("/api/profile", {
              method: "PUT",
              body: { facts, source_file_id: approved.source_file_id, version: data.version },
            }),
          );
          await refresh();
          rest();
          offerUndo({
            eventId: saved.event_id,
            saved: "Profile saved",
            undone: "Change undone",
            refresh,
          });
        },
      };
    }
    if (reads) return { status: "reading", file };
    if (stopped) {
      return {
        status: "stopped",
        file,
        waiting: stopped.state === "queued",
        message: stopped.problem ?? "Reading stopped before it finished. Try again.",
        onReplace: () => choose(),
        onKeep: approved ? () => setDismissed(stopped.job_id) : undefined,
        onRetry: () => {
          void retryReading(stopped.job_id)
            .then(refresh)
            .catch((error: unknown) => showToast(reasonFor(error)));
        },
      };
    }
    if (suggestion) {
      const address = `/api/proposals/${suggestion.proposal_id}`;
      return {
        status: "review",
        file,
        facts: suggestion.facts,
        approved: approved?.facts ?? null,
        dropped: suggestion.dropped,
        onReplace: () => choose(),
        onApprove: async (facts) => {
          const done = await decide(() =>
            api<{ event_id: string | null }>(`${address}/approve`, {
              method: "POST",
              body: { edited_payload: { facts, source_file_id: suggestion.source_file_id } },
            }),
          );
          await refresh();
          offerUndo({
            eventId: done.event_id,
            saved: "Profile approved",
            undone: "Approval undone",
            refresh,
          });
        },
        onDiscard: async () => {
          await decide(() => api(`${address}/reject`, { method: "POST" }));
          await refresh();
          showToast("Suggestions discarded");
        },
      };
    }
    if (approved && summary) {
      return {
        status: "approved",
        // The card is there from the start, so nothing jumps when the file's name arrives.
        file: approved.source_file_id ? file : null,
        summary,
        version: approved,
        approvedOn: approved.approved_at ? mediumDate(new Date(approved.approved_at)) : "",
        onEdit: () => setLocal({ kind: "editing" }),
        onReplace: () => choose(),
      };
    }
    return { status: "choose", onFile: upload };
  }

  const shown = state();
  const approved = Boolean(data?.approved);
  // The step holds the main button then, so the one below it is plain.
  const busyStep = ["identity", "review", "editing"].includes(shown.status);
  const toStep2 = () => {
    saveSetupStep(2);
    router.push("/onboarding?step=2");
  };

  return (
    <OnboardingFrame
      step={1}
      next={{ label: "Continue", onClick: toStep2, disabled: !approved }}
      phoneNext={{
        label: approved ? "Continue" : "I’ll add it later",
        onClick: toStep2,
        quiet: busyStep,
      }}
    >
      <div className="flex flex-col gap-4 md:gap-[22px]">
        <ResumeHeading />
        <ResumeStep
          state={shown}
          aiNotReady={privacy.data ? (NOT_READY[privacy.data.status] ?? null) : null}
        />
      </div>
    </OnboardingFrame>
  );
}
