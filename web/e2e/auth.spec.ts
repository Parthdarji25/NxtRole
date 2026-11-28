import { expect, test, type Page } from "@playwright/test";

import { EMAILS, password, type Account } from "./accounts";
import { DESKTOP, open, PHONE, signIn } from "./helpers";

const heading = (page: Page) => page.getByRole("heading", { level: 1 });

async function typeSignIn(page: Page, account: Account, secret = password()) {
  await page.getByLabel("Email").fill(EMAILS[account]);
  await page.getByLabel("Password", { exact: true }).fill(secret);
}

test.use({ viewport: DESKTOP });

test("a visitor signs in and returns to the screen they asked for (FR-006)", async ({ page }) => {
  await page.goto("/jobs");
  await expect(page).toHaveURL(/\/login\?next=%2Fjobs$/);

  await typeSignIn(page, "owner");
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page).toHaveURL(/\/jobs$/);
  await expect(heading(page)).toHaveText("Jobs");
});

test("an address of another website is never followed after signing in", async ({ page }) => {
  await page.goto("/login?next=https://evil.example/");
  await typeSignIn(page, "owner");
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page).toHaveURL(/127\.0\.0\.1:\d+\/today$/);
});

test("reloading keeps the sign-in, with the token out of reach of other scripts", async ({
  page,
  context,
}) => {
  await signIn(page);
  await open(page, "/today");
  await page.reload();
  await expect(heading(page)).toHaveText("Good morning.");

  const [cookie] = await context.cookies("http://127.0.0.1:3100/api/auth/refresh");
  expect(cookie).toMatchObject({
    name: "__Secure-nr_refresh",
    httpOnly: true,
    secure: true,
    sameSite: "Strict",
    path: "/api/auth",
  });
  // The page's own scripts can see no token anywhere.
  const visible = await page.evaluate(() =>
    JSON.stringify([{ ...localStorage }, { ...sessionStorage }, document.cookie]),
  );
  expect(visible).not.toContain(cookie!.value);
  expect(visible).not.toMatch(/eyJ[\w-]+\.eyJ/);
});

test("a signed-in owner who opens the sign-in screen goes straight in", async ({ page }) => {
  await signIn(page);

  await page.goto("/login");

  await expect(page).toHaveURL(/\/today$/);
});

test("wrong details get one plain message, and five tries lock", async ({ page }) => {
  await page.goto("/login");
  // An address without an account behaves like one with an account.
  await page.getByLabel("Email").fill(`nobody-${Date.now()}@example.com`);
  await page.getByLabel("Password", { exact: true }).fill("not the password at all");
  const button = page.getByRole("button", { name: "Sign in" });
  const problem = page.locator("form [role=alert]");

  for (let attempt = 1; attempt <= 4; attempt++) {
    await button.click();
    await expect(problem).toHaveText("That email or password is not right.");
    await expect(button).toBeEnabled();
  }
  await button.click();

  await expect(problem).toContainText("Too many wrong attempts. Try again in 15 minutes.");
  await expect(page).toHaveURL(/\/login$/);
});

test("@E-34 a double click signs in once", async ({ page }) => {
  let requests = 0;
  await page.route("**/api/auth/login", async (route) => {
    requests += 1;
    await new Promise((resolve) => setTimeout(resolve, 500));
    await route.continue();
  });
  await page.goto("/login");
  await typeSignIn(page, "owner");

  await page.getByRole("button", { name: "Sign in" }).dblclick();

  await expect(page).toHaveURL(/\/today$/);
  expect(requests).toBe(1);
});

test("@E-23 two tabs opening at once both stay signed in", async ({ page, context }) => {
  await signIn(page);
  const second = await context.newPage();

  await Promise.all([page.goto("/jobs"), second.goto("/pipeline")]);
  await Promise.all([expect(heading(page)).toHaveText("Jobs"), page.reload(), second.reload()]);

  await expect(heading(page)).toHaveText("Jobs");
  await expect(heading(second)).toHaveText("Pipeline");
});

test("signing out in one tab signs out the other, and going back shows nothing", async ({
  page,
  context,
}) => {
  await signIn(page);
  await open(page, "/jobs");
  const second = await context.newPage();
  await open(second, "/pipeline");

  await open(page, "/settings?section=accounts");
  await page.getByRole("button", { name: "Sign out", exact: true }).last().click();

  await expect(page).toHaveURL(/\/login$/);
  await expect(second).toHaveURL(/\/login$/);
  await page.goBack();
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByRole("heading", { name: "Settings" })).toHaveCount(0);
});

test("the phone's More page signs out", async ({ page }) => {
  await page.setViewportSize(PHONE);
  await signIn(page);
  await open(page, "/more");

  await page.getByRole("button", { name: "Sign out" }).click();

  await expect(page).toHaveURL(/\/login$/);
});

test("@E-56 an access token that runs out mid-use is renewed unnoticed", async ({ page }) => {
  await signIn(page);
  await open(page, "/today");
  let refreshes = 0;
  page.on("request", (request) => {
    if (request.url().endsWith("/api/auth/refresh")) refreshes += 1;
  });
  // The first list request is answered as if the 15 minutes were over.
  let expired = false;
  await page.route("**/api/account/sessions", async (route) => {
    if (expired) return route.continue();
    expired = true;
    await route.fulfill({
      status: 401,
      json: { detail: { code: "token_expired", message: "Your sign-in needs refreshing." } },
    });
  });

  // Settings sits below the main list in the side menu.
  await page.getByRole("link", { name: "Settings", exact: true }).click();
  await page.getByRole("link", { name: "Accounts" }).click();

  await expect(page.getByText("This device")).toBeVisible();
  await expect(page).toHaveURL(/section=accounts/);
  expect(refreshes).toBe(1);
});

test("when the API cannot be reached the screen says so and can try again", async ({ page }) => {
  await signIn(page);
  await page.route("**/api/auth/refresh", (route) => route.abort());
  await page.goto("/jobs");
  await expect(page.getByRole("alert").filter({ hasText: "cannot be reached" })).toBeVisible();

  await page.unroute("**/api/auth/refresh");
  await page.getByRole("button", { name: "Try again" }).click();

  await expect(heading(page)).toHaveText("Jobs");
});
