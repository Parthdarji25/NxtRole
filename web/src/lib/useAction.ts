"use client";

import { useRef, useState } from "react";

import { ApiError } from "./http";

export const UNEXPECTED = "Something went wrong. Please try again.";

/** A failure in words that can be shown. */
export const reasonFor = (error: unknown): string =>
  error instanceof ApiError ? error.message : UNEXPECTED;

/**
 * Runs something that talks to the API, one at a time: a second click while it runs is
 * ignored, and a failure is kept as a message to show.
 */
export function useAction<Args extends unknown[]>(task: (...args: Args) => Promise<unknown>) {
  const running = useRef(false);
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  /** Returns true when the task succeeded. */
  async function run(...args: Args): Promise<boolean> {
    if (running.current) return false;
    running.current = true;
    setBusy(true);
    setProblem(null);
    try {
      await task(...args);
      return true;
    } catch (error) {
      setProblem(reasonFor(error));
      return false;
    } finally {
      running.current = false;
      setBusy(false);
    }
  }

  return { run, busy, problem, clear: () => setProblem(null) };
}
