"use client";

import { Screen } from "@/components/layout/screen";
import { EmptyScreenState } from "@/components/states/EmptyScreenState";
import { EMPTY_STATES } from "@/content/emptyStates";
import { useSession } from "@/lib/useSession";

/** "Good morning, <name>." once the owner has saved a name in Settings (D-050). */
export function greeting(name: string | null): string {
  return name ? `Good morning, ${name}.` : "Good morning.";
}

export function TodayScreen({ kicker }: { kicker: string }) {
  const session = useSession();
  const name = session.status === "signedIn" ? session.user.display_name : null;
  return (
    <Screen
      kicker={kicker}
      title={greeting(name)}
      lead="Your short list appears here every morning."
    >
      <EmptyScreenState content={EMPTY_STATES.today} />
    </Screen>
  );
}
