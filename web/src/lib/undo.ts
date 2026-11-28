/** "Saved. Undo": takes a change back through its history event (golden rule 2). */
import { showToast, showUndoToast } from "@/components/ui/toast";

import { api } from "./api";
import { reasonFor } from "./useAction";

export function offerUndo({
  eventId,
  saved,
  undone,
  refresh,
}: {
  /** null when nothing changed, so there is nothing to take back. */
  eventId: string | null;
  saved: string;
  undone: string;
  /** Reads what is stored now, so the screen shows it. */
  refresh: () => Promise<unknown>;
}): void {
  if (!eventId) return;
  async function undo() {
    try {
      await api(`/api/events/${eventId}/undo`, { method: "POST" });
      await refresh();
      showToast(undone);
    } catch (error) {
      showToast(reasonFor(error));
    }
  }
  showUndoToast(saved, () => void undo());
}
