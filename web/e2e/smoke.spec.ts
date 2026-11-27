import { expect, test } from "@playwright/test";

test("home page shows the database and Redis as ok through the /api forwarding", async ({
  page,
}) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "NxtRole" })).toBeVisible();
  await expect(page.getByRole("status")).toHaveText("database ok, redis ok");
});

test("pages are sent with the security headers", async ({ request }) => {
  const response = await request.get("/");
  const headers = response.headers();

  expect(headers["x-content-type-options"]).toBe("nosniff");
  expect(headers["x-frame-options"]).toBe("DENY");
  expect(headers["content-security-policy"]).toContain("frame-ancestors 'none'");
  expect(headers["x-powered-by"]).toBeUndefined();
});
