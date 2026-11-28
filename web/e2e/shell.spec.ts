import { expect, test } from "@playwright/test";

import { DESKTOP, open, PHONE, ROUTES, sideScroll, signIn, visit } from "./helpers";

test("@E-51 narrow phones and 200% zoom have no sideways scrolling", async ({ page }) => {
  test.slow();
  // 320px is the narrowest phone; 720px is a 1440px screen zoomed to 200%.
  for (const width of [320, 720]) {
    await page.setViewportSize({ width, height: 700 });
    for (const route of ROUTES) {
      await visit(page, route);
      expect(await sideScroll(page), `${route.path} at ${width}px`).toBe(0);
    }
  }
});

test("@E-76 a 60-character heading wraps without breaking the layout", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 700 });
  await signIn(page);
  await open(page, "/today");
  await page.locator("h1").evaluate((heading) => {
    heading.textContent = "Averylongcompanynamewithoutanyspacesthatmuststillwrapnicely1";
  });

  expect(await sideScroll(page)).toBe(0);
});

test("the side menu shows icons only between 768px and 1023px (D-014)", async ({ page }) => {
  await signIn(page);
  await open(page, "/jobs");
  const jobs = page.getByRole("navigation", { name: "Main" }).getByRole("link", { name: "Jobs" });

  await page.setViewportSize({ width: 900, height: 800 });
  expect((await jobs.boundingBox())!.width).toBeLessThan(60);

  await page.setViewportSize(DESKTOP);
  expect((await jobs.boundingBox())!.width).toBeGreaterThan(200);
});

test("phones get the tab bar, and More reaches the other screens", async ({ page }) => {
  await page.setViewportSize(PHONE);
  await signIn(page);
  await open(page, "/today");
  const tabs = page.getByRole("navigation", { name: "Main" });
  await expect(tabs.getByRole("link")).toHaveText(["Today", "Jobs", "Pipeline", "Prepare", "More"]);

  await tabs.getByRole("link", { name: "More" }).click();
  await page.getByRole("link", { name: /^Studio/ }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Studio");
  await expect(tabs.getByRole("link", { name: "More" })).toHaveAttribute("aria-current", "page");
});

test("every control on a screen can be reached with the keyboard", async ({ page }) => {
  await page.setViewportSize(DESKTOP);
  for (const path of ["/today", "/settings?section=accounts", "/login", "/"]) {
    await visit(
      page,
      ROUTES.find((route) => route.path === path)!,
    );
    // Tag every control that should be reachable.
    const expected = await page.evaluate(() => {
      const controls = [
        ...document.querySelectorAll<HTMLElement>("a[href], button, input, select"),
      ];
      const wanted = controls.filter(
        (element) =>
          element.checkVisibility() &&
          !element.hasAttribute("disabled") &&
          // Tab lists move with the arrow keys; only the selected tab is in the tab order.
          element.getAttribute("tabindex") !== "-1",
      );
      wanted.forEach((element, index) => element.setAttribute("data-reach", String(index)));
      return wanted.length;
    });
    const reached = new Set<string>();
    for (let press = 0; press < expected + 15; press++) {
      await page.keyboard.press("Tab");
      const id = await page.evaluate(() => document.activeElement?.getAttribute("data-reach"));
      if (id) reached.add(id);
    }
    expect(reached.size, path).toBe(expected);
  }
});

test.describe("theme", () => {
  test.use({ colorScheme: "dark" });

  test("@E-77 follows a dark system on the first visit and keeps the owner's choice", async ({
    page,
  }) => {
    // Records the theme at the first moment the page body exists, to catch a flash.
    await page.addInitScript(() => {
      new MutationObserver((_changes, observer) => {
        if (!document.body) return;
        (window as unknown as { firstTheme: string | null }).firstTheme =
          document.documentElement.getAttribute("data-theme");
        observer.disconnect();
      }).observe(document, { childList: true, subtree: true });
    });
    await signIn(page);
    await open(page, "/today");
    expect(
      await page.evaluate(() => (window as unknown as { firstTheme: string }).firstTheme),
    ).toBe("dark");

    await page.getByRole("group", { name: "Theme" }).getByRole("button", { name: "Light" }).click();
    await page.reload();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  });
});

test("@E-51 reduced motion switches animations off", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await open(page, "/");
  const animation = await page
    .locator("h1")
    .evaluate((element) => getComputedStyle(element).animationName);

  expect(animation).toBe("none");
});

test("@E-34 a slow screen change shows placeholders, not a blank page", async ({ page }) => {
  await page.setViewportSize(DESKTOP);
  await signIn(page);
  await open(page, "/today");
  // Hold back the data for the next screen.
  await page.route("**/jobs**", async (route) => {
    if (route.request().headers()["next-router-prefetch"]) return route.abort();
    await new Promise((resolve) => setTimeout(resolve, 2000));
    await route.continue();
  });

  await page.getByRole("navigation", { name: "Main" }).getByRole("link", { name: "Jobs" }).click();

  await expect(page.getByRole("status").filter({ hasText: "Loading" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Jobs");
});

test("each screen shows at most one blue primary button", async ({ page }) => {
  test.slow();
  for (const viewport of [DESKTOP, PHONE]) {
    await page.setViewportSize(viewport);
    for (const route of ROUTES) {
      await visit(page, route);
      const shown = await page.locator('[data-variant="primary"]:visible').count();
      // The Landing mocks draw two: "Open the app" in the header and "Next" in the tour.
      expect(shown, `${route.path} at ${viewport.width}px`).toBeLessThanOrEqual(
        route.path === "/" ? 2 : 1,
      );
    }
  }
});

test("@E-78 an unknown address shows the 404 page with a way back", async ({ page }) => {
  await signIn(page);
  const response = await page.goto("/no-such-page");

  expect(response!.status()).toBe(404);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("This page is not here.");
  await page.getByRole("link", { name: "Go to Today" }).click();
  await expect(page).toHaveURL(/\/today$/);
});

test("@E-79 the showroom does not exist in the production build", async ({ request }) => {
  expect((await request.get("/design")).status()).toBe(404);
  expect((await request.get("/design/states")).status()).toBe(404);
});
