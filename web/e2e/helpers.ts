import { expect, type Page } from "@playwright/test";

import { EMAILS, password, type Account } from "./accounts";
import routes from "./routes.json" with { type: "json" };

export type Route = {
  path: string;
  name: string;
  desktopMock: string | null;
  phoneMock: string | null;
  signedIn?: boolean;
};

export const ROUTES: Route[] = routes;
export const DESKTOP = { width: 1440, height: 900 };
export const PHONE = { width: 390, height: 844 };
export const THEMES = ["light", "dark"] as const;

/**
 * Signs this browser in without using the screen: the refresh cookie lands in the browser,
 * and the next screen restores the sign-in from it, as after a real visit.
 */
export async function signIn(page: Page, account: Account = "owner"): Promise<void> {
  const response = await page.request.post("/api/auth/login", {
    data: { email: EMAILS[account], password: password() },
  });
  expect(response.status()).toBe(200);
}

/** Opens a page and waits until it is fully drawn. */
export async function open(page: Page, path: string): Promise<void> {
  await page.goto(path, { waitUntil: "networkidle" });
  // The placeholders are gone.
  await expect(page.locator('[aria-busy="true"]')).toHaveCount(0);
  await page.evaluate(() => document.fonts.ready);
}

/** Signs in or out as the route needs, then opens it. */
export async function visit(page: Page, route: Route, account: Account = "owner"): Promise<void> {
  if (route.signedIn) await signIn(page, account);
  else await page.context().clearCookies();
  await open(page, route.path);
}

/** How far the page is wider than the screen, in pixels. 0 means no sideways scrolling. */
export function sideScroll(page: Page): Promise<number> {
  return page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
}
