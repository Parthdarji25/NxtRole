import { expect, test } from "@playwright/test";

import { signIn } from "./helpers";

test("the landing page leads to sign in", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { level: 1 })).toContainText("Sleep tonight.");
  await page.getByRole("banner").getByRole("link", { name: "Open the app" }).click();
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByLabel("Password", { exact: true })).toBeVisible();
});

test("the API, database and Redis answer through the /api forwarding", async ({ request }) => {
  const response = await request.get("/api/health/ready");

  expect(response.status()).toBe(200);
  expect(await response.json()).toEqual({ database: "ok", redis: "ok" });
});

test("pages are sent with the security headers and run without blocked scripts", async ({
  page,
}) => {
  await signIn(page);
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  const response = await page.goto("/today");
  const headers = response!.headers();

  expect(headers["x-content-type-options"]).toBe("nosniff");
  expect(headers["x-frame-options"]).toBe("DENY");
  expect(headers["content-security-policy"]).toContain("frame-ancestors 'none'");
  expect(headers["content-security-policy"]).toContain("'nonce-");
  expect(headers["x-powered-by"]).toBeUndefined();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Good morning.");
  await page.keyboard.press("Control+k");
  await expect(page.getByRole("searchbox")).toBeFocused();
  expect(errors).toEqual([]);
});
