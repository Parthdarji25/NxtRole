import type { Page } from "@playwright/test";

import routes from "./routes.json" with { type: "json" };

export const ROUTES = routes;
export const DESKTOP = { width: 1440, height: 900 };
export const PHONE = { width: 390, height: 844 };
export const THEMES = ["light", "dark"] as const;

/** Opens a page and waits until it is fully drawn. */
export async function open(page: Page, path: string): Promise<void> {
  await page.goto(path, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
}

/** How far the page is wider than the screen, in pixels. 0 means no sideways scrolling. */
export function sideScroll(page: Page): Promise<number> {
  return page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
}
