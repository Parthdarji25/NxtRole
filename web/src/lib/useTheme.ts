"use client";

import { useSyncExternalStore } from "react";

import { chooseTheme, currentTheme, subscribeToTheme, type Theme } from "./theme";

/** The theme on the page. `null` while rendering on the server, which cannot know it. */
export function useTheme(): [Theme | null, (theme: Theme) => void] {
  const theme = useSyncExternalStore<Theme | null>(subscribeToTheme, currentTheme, () => null);
  return [theme, chooseTheme];
}
