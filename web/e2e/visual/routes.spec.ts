import { expect, test } from "@playwright/test";

import { DESKTOP, PHONE, ROUTES, THEMES, visit } from "../helpers";

// Pictures differ slightly between Windows and Linux, so they are compared on this machine only
// (D-046). After an intended change:  pnpm e2e:update-pictures
test.skip(Boolean(process.env.CI), "picture comparisons run locally only");

for (const [device, viewport] of [
  ["desktop", DESKTOP],
  ["phone", PHONE],
] as const) {
  for (const theme of THEMES) {
    test.describe(`${device} ${theme}`, () => {
      test.use({ viewport, colorScheme: theme, contextOptions: { reducedMotion: "reduce" } });

      for (const route of ROUTES) {
        test(`${route.name} looks as approved`, async ({ page }) => {
          // The account screen lists signed-in devices, so each picture has its own account.
          await visit(page, route, route.name === "accounts" ? `${device}-${theme}` : "owner");

          if (route.name === "accounts") {
            // Sign-in times change every run, so the picture gets fixed words instead.
            await page
              .getByText(/^Last used/)
              .evaluate((line) => (line.textContent = "Last used today · signed in today"));
          }

          if (route.path === "/today") {
            // Today's date changes every day, so the picture gets fixed words instead.
            await page
              .locator(".kicker:visible")
              .first()
              .evaluate((label) => (label.textContent = "Today's date"));
          }

          await expect(page).toHaveScreenshot(`${route.name}-${device}-${theme}.png`, {
            fullPage: true,
            maxDiffPixelRatio: 0.001,
          });
        });
      }
    });
  }
}
