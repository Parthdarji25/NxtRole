"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";

import { ErrorState, ListSkeleton } from "@/components/states/states";
import { getProfile, PROFILE } from "@/features/profile/api";
import { ApiError } from "@/lib/api";
import { offerUndo } from "@/lib/undo";
import { reasonFor } from "@/lib/useAction";

import { getPreferences, PREFERENCES, RULES, savePreferences } from "./api";
import { SearchSettings } from "./SearchSettings";

/** Settings > Search, connected to the API. */
export function SearchSettingsContainer() {
  const queries = useQueryClient();
  const preferences = useQuery({ queryKey: PREFERENCES, queryFn: getPreferences });
  const profile = useQuery({ queryKey: PROFILE, queryFn: getProfile });
  const saved = preferences.data;

  if (!saved || !profile.data) {
    const failed = preferences.isError ? preferences : profile.isError ? profile : null;
    return failed ? (
      <ErrorState onRetry={() => void failed.refetch()}>{reasonFor(failed.error)}</ErrorState>
    ) : (
      <ListSkeleton rows={4} label="Loading your search" />
    );
  }

  const refresh = () =>
    Promise.all([
      queries.invalidateQueries({ queryKey: PREFERENCES }),
      queries.invalidateQueries({ queryKey: RULES }),
    ]);

  return (
    <SearchSettings
      // A newer saved version starts the form again from what is stored.
      key={saved.version}
      saved={saved}
      resumeExperience={
        profile.data.approved ? (profile.data.summary?.experience_years ?? null) : undefined
      }
      onSave={async (values) => {
        try {
          const done = await savePreferences(values, saved.version);
          queries.setQueryData(PREFERENCES, done.preferences);
          void queries.invalidateQueries({ queryKey: RULES });
          offerUndo({
            eventId: done.event_id,
            saved: "Search saved",
            undone: "Change undone",
            refresh,
          });
        } catch (error) {
          // Changed elsewhere: show what is stored, so that saving again can work.
          if (error instanceof ApiError && error.code === "conflict") await refresh();
          throw error;
        }
      }}
    />
  );
}
