"use client";

import { useSyncExternalStore } from "react";

import { getServerSession, getSession, subscribe, type Session } from "./session";

/** Who is signed in. The component redraws when that changes. */
export function useSession(): Session {
  return useSyncExternalStore(subscribe, getSession, getServerSession);
}
