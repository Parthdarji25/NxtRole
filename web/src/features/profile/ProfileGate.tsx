import { EmptyScreenState } from "@/components/states/EmptyScreenState";
import { PROFILE_STATES } from "@/content/profileStates";

/** Shown where approved facts are needed and there are none yet (FR-016). */
export function ProfileGate() {
  return <EmptyScreenState content={PROFILE_STATES.needed} />;
}
