import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { DESKTOP, PHONE, ROUTES, sideScroll, THEMES, visit } from "./helpers";

const WCAG = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

for (const [device, viewport] of [
  ["desktop", DESKTOP],
  ["phone", PHONE],
] as const) {
  for (const theme of THEMES) {
    test.describe(`${device} ${theme}`, () => {
      test.use({ viewport, colorScheme: theme, contextOptions: { reducedMotion: "reduce" } });

      for (const route of ROUTES) {
        test(`@E-51 ${route.name} passes accessibility checks`, async ({ page }) => {
          await visit(page, route);

          const result = await new AxeBuilder({ page }).withTags(WCAG).analyze();

          expect(
            result.violations.map((violation) => `${violation.id}: ${violation.nodes[0]?.target}`),
          ).toEqual([]);
          await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
          await expect(page.locator("h1:visible")).toHaveCount(1);
          expect(await sideScroll(page)).toBe(0);
        });
      }
    });
  }
}
