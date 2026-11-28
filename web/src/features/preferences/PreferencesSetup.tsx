"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ErrorState, ListSkeleton } from "@/components/states/states";
import { FormProblem } from "@/components/ui/form-problem";
import { OnboardingFrame } from "@/features/onboarding/OnboardingFrame";
import { getProfile, PROFILE } from "@/features/profile/api";
import type { Profile } from "@/features/profile/types";
import { ApiError } from "@/lib/api";
import { offerUndo } from "@/lib/undo";
import { reasonFor, useAction } from "@/lib/useAction";

import { getPreferences, PREFERENCES, savePreferences, saveSetupStep, valuesOf } from "./api";
import { check, toDraft, type Draft, type DraftErrors, type Preferences } from "./draft";
import { PreferencesStep } from "./PreferencesStep";
import { suggestionsFrom } from "./suggestions";

const BACK = { label: "Back", href: "/onboarding?step=1" };

function SetupForm({ saved, profile }: { saved: Preferences; profile: Profile }) {
  const router = useRouter();
  const queries = useQueryClient();
  const suggestions = suggestionsFrom(
    profile.approved?.facts ?? null,
    profile.summary?.latest_role ?? null,
  );
  const [draft, setDraft] = useState<Draft>(() => {
    const start = toDraft(saved);
    // Nothing saved yet: the current role and city are filled in, ready to change.
    if (saved.version > 0) return start;
    const home = suggestions.places[0];
    return {
      ...start,
      titles: suggestions.titles.slice(0, 1),
      // With no city in the resume, the only suggestion is remote work: leave it unchosen.
      places: suggestions.places.length > 1 && home ? [home] : [],
    };
  });
  const [errors, setErrors] = useState<DraftErrors>({});
  const [part, setPart] = useState<"roles" | "pay">("roles");

  const refresh = () => queries.invalidateQueries({ queryKey: PREFERENCES });
  const action = useAction(async () => {
    const result = check(draft);
    setErrors(result.errors ?? {});
    if (!result.values) {
      // On a phone the problem may be on the other view.
      setPart(result.errors.titles ? "roles" : "pay");
      return;
    }
    try {
      const done = await savePreferences(
        // Fields this step does not show are sent back as they are.
        { ...valuesOf(saved), ...result.values },
        saved.version,
      );
      queries.setQueryData(PREFERENCES, done.preferences);
      offerUndo({
        eventId: done.event_id,
        saved: "Search saved",
        undone: "Change undone",
        refresh,
      });
    } catch (error) {
      // Changed elsewhere: read the newer version, so that saving again can work.
      if (error instanceof ApiError && error.code === "conflict") await refresh();
      throw error;
    }
    saveSetupStep(3);
    router.push("/onboarding?step=3");
  });

  const noTitle = draft.titles.length === 0;
  const next = {
    label: "Continue",
    onClick: () => void action.run(),
    disabled: noTitle,
    busy: action.busy,
  };

  return (
    <OnboardingFrame
      step={2}
      back={BACK}
      next={next}
      phoneBack={part === "pay" ? { label: "Back", onClick: () => setPart("roles") } : BACK}
      phoneNext={
        part === "roles"
          ? { label: "Continue", onClick: () => setPart("pay"), disabled: noTitle }
          : next
      }
    >
      <div className="flex flex-col gap-4">
        <PreferencesStep
          draft={draft}
          onChange={setDraft}
          errors={errors}
          phonePart={part}
          suggestions={suggestions}
        />
        <FormProblem>{action.problem}</FormProblem>
      </div>
    </OnboardingFrame>
  );
}

/** Onboarding step 2, connected to the API. */
export function PreferencesSetup() {
  const preferences = useQuery({ queryKey: PREFERENCES, queryFn: getPreferences });
  const profile = useQuery({ queryKey: PROFILE, queryFn: getProfile });

  if (preferences.data && profile.data) {
    return <SetupForm saved={preferences.data} profile={profile.data} />;
  }
  const failed = preferences.isError ? preferences : profile.isError ? profile : null;
  return (
    <OnboardingFrame step={2} back={BACK} next={{ label: "Continue", disabled: true }}>
      {failed ? (
        <ErrorState onRetry={() => void failed.refetch()}>{reasonFor(failed.error)}</ErrorState>
      ) : (
        <ListSkeleton rows={3} label="Loading your search" />
      )}
    </OnboardingFrame>
  );
}
