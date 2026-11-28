"use client";

import { useQuery } from "@tanstack/react-query";

import { ErrorState, ListSkeleton } from "@/components/states/states";
import { getPrivacy, PRIVACY } from "@/features/profile/api";
import { mediumDate } from "@/lib/dates";
import { reasonFor } from "@/lib/useAction";

import { PrivacySettings } from "./PrivacySettings";

/** Settings > Privacy, connected to the API. */
export function PrivacyContainer() {
  const privacy = useQuery({ queryKey: PRIVACY, queryFn: getPrivacy });
  if (!privacy.data) {
    return privacy.isError ? (
      <ErrorState onRetry={() => void privacy.refetch()}>{reasonFor(privacy.error)}</ErrorState>
    ) : (
      <ListSkeleton rows={3} label="Loading privacy settings" />
    );
  }
  const confirmed = privacy.data.zero_data_retention_confirmed_on;
  return <PrivacySettings confirmedOn={confirmed ? mediumDate(new Date(confirmed)) : null} />;
}
