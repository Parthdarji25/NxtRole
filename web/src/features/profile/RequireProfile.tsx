"use client";

import { useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";

import { ErrorState, ListSkeleton } from "@/components/states/states";
import { reasonFor } from "@/lib/useAction";

import { getProfile, PROFILE } from "./api";
import { ProfileGate } from "./ProfileGate";

/** Shows what is inside only when there are approved facts to work from (FR-016). */
export function RequireProfile({ children }: { children: ReactNode }) {
  const profile = useQuery({ queryKey: PROFILE, queryFn: getProfile });
  if (!profile.data) {
    return profile.isError ? (
      <ErrorState onRetry={() => void profile.refetch()}>{reasonFor(profile.error)}</ErrorState>
    ) : (
      <ListSkeleton rows={1} label="Loading your profile" />
    );
  }
  return profile.data.approved ? children : <ProfileGate />;
}
