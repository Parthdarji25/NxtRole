"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";

import { showToast, showUndoToast } from "@/components/ui/toast";
import { api, ApiError } from "@/lib/api";
import { endSession, signOut, updateUser, type User } from "@/lib/session";
import { UNEXPECTED } from "@/lib/useAction";
import { useSession } from "@/lib/useSession";

import { AccountView, type AccountActions, type Device, type DeviceList } from "./AccountView";

const DEVICES = ["account", "sessions"];

const reason = (error: unknown) => (error instanceof ApiError ? error.message : UNEXPECTED);

/** Reads the profile again, so the screen shows what is stored now. */
async function reloadUser(): Promise<void> {
  updateUser(await api<User>("/api/me"));
}

async function undoRename(eventId: string): Promise<void> {
  try {
    await api(`/api/events/${eventId}/undo`, { method: "POST" });
    await reloadUser();
    showToast("Name put back");
  } catch (error) {
    showToast(reason(error));
  }
}

/** Settings > Accounts, connected to the API. */
export function AccountSettings() {
  const session = useSession();
  const queries = useQueryClient();
  const sessions = useQuery({
    queryKey: DEVICES,
    queryFn: () => api<{ items: Device[] }>("/api/account/sessions"),
  });

  if (session.status !== "signedIn") return null;
  const { user } = session;

  const devices: DeviceList = sessions.data
    ? { status: "ready", items: sessions.data.items }
    : sessions.isError
      ? { status: "error", message: reason(sessions.error), retry: () => void sessions.refetch() }
      : { status: "loading" };

  const actions: AccountActions = {
    saveName: async (name) => {
      try {
        const saved = await api<{ user: User; event_id: string | null }>("/api/account/profile", {
          method: "PATCH",
          body: { display_name: name, version: user.version },
        });
        updateUser(saved.user);
        const eventId = saved.event_id;
        if (eventId) showUndoToast("Name saved", () => void undoRename(eventId));
      } catch (error) {
        // Someone else changed it: show theirs, so that trying again can work.
        if (error instanceof ApiError && error.code === "conflict") await reloadUser();
        throw error;
      }
    },
    changePassword: async (values) => {
      await api("/api/account/password", { method: "POST", body: values });
      showToast("Password changed. Your other devices were signed out.");
      void queries.invalidateQueries({ queryKey: DEVICES });
    },
    signOutDevice: async (familyId) => {
      try {
        await api(`/api/account/sessions/${familyId}`, { method: "DELETE" });
        showToast("That device was signed out");
      } finally {
        // Also when it had already signed out: the list shows the truth.
        await queries.invalidateQueries({ queryKey: DEVICES });
      }
    },
    signOut,
    signOutEverywhere: async () => {
      await api("/api/auth/logout-all", { method: "POST" });
      endSession(true);
    },
  };

  return <AccountView user={user} devices={devices} actions={actions} />;
}
