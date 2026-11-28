import { expect, test, type Page } from "@playwright/test";

import { EMAILS, password, recoveryCode } from "./accounts";
import { DESKTOP, open, signIn } from "./helpers";

const NEW_PASSWORD = "a different long sentence 42";
const RECOVERED_PASSWORD = "the recovered long sentence";

test.use({ viewport: DESKTOP });

const sideMenu = (page: Page) => page.getByRole("navigation", { name: "Main" });

test("saving the name greets the owner, and Undo takes it back", async ({ page }) => {
  await signIn(page, "editor");
  await open(page, "/settings?section=accounts");

  await page.getByLabel("Your name").fill("Asha");
  await page.getByRole("button", { name: "Save name" }).click();
  await expect(page.getByText("Name saved")).toBeVisible();
  await sideMenu(page).getByRole("link", { name: "Today" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Good morning, Asha.");

  await page.getByRole("button", { name: "Undo" }).click();

  await expect(page.getByText("Name put back")).toBeVisible();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Good morning.");
});

// These end sign-ins, so they use their own account and run in this order.
test.describe.serial("passwords and devices", () => {
  test("a device can be signed out from another one", async ({ page, browser }) => {
    const elsewhere = await browser.newContext({
      userAgent: "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0) Version/26.0 Safari/604.1",
    });
    const phone = await elsewhere.newPage();
    await signIn(phone, "careful");
    await open(phone, "/today");
    await signIn(page, "careful");
    await open(page, "/settings?section=accounts");

    await page.getByRole("button", { name: "Sign out Safari on iPhone" }).first().click();

    await expect(page.getByText("That device was signed out")).toBeVisible();
    await expect(page.getByRole("button", { name: "Sign out Safari on iPhone" })).toHaveCount(0);
    // Its next request is refused at once.
    await phone.reload();
    await expect(phone).toHaveURL(/\/login/);
    await elsewhere.close();
  });

  test("changing the password signs the other devices out", async ({ page, browser }) => {
    const elsewhere = await browser.newContext();
    const other = await elsewhere.newPage();
    await signIn(other, "careful");
    await signIn(page, "careful");
    await open(page, "/settings?section=accounts");

    await page.getByRole("button", { name: "Change password" }).click();
    const drawer = page.getByRole("dialog");
    await drawer.getByLabel("Current password", { exact: true }).fill(password());
    await drawer.getByLabel("New password", { exact: true }).fill(NEW_PASSWORD);
    await drawer.getByLabel("New password again", { exact: true }).fill(NEW_PASSWORD);
    await drawer.getByRole("button", { name: "Change password" }).click();

    await expect(page.getByText("Password changed.")).toBeVisible();
    await expect(drawer).toHaveCount(0);
    await open(other, "/jobs").catch(() => {});
    await expect(other).toHaveURL(/\/login/);
    await page.reload();
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("Settings");
    await elsewhere.close();
  });

  test("sign out everywhere ends this device too", async ({ page }) => {
    await page.goto("/login?next=/settings?section=accounts");
    await page.getByLabel("Email").fill(EMAILS.careful);
    await page.getByLabel("Password", { exact: true }).fill(NEW_PASSWORD);
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByText("This device")).toBeVisible();

    await page.getByRole("button", { name: "Sign out everywhere" }).click();
    await page.getByRole("dialog").getByRole("button", { name: "Sign out everywhere" }).click();

    await expect(page).toHaveURL(/\/login$/);
    await page.goto("/today");
    await expect(page).toHaveURL(/\/login$/);
  });

  test("@E-25 the recovery code sets a new password and gives a new code", async ({ page }) => {
    await open(page, "/login/recover");
    await page.getByLabel("Email").fill(EMAILS.careful);
    await page.getByLabel("Recovery code").fill(recoveryCode().toLowerCase());
    await page.getByLabel("New password", { exact: true }).fill(RECOVERED_PASSWORD);
    await page.getByLabel("New password again", { exact: true }).fill(RECOVERED_PASSWORD);
    await page.getByRole("button", { name: "Set new password" }).click();

    const code = page.locator("code").first();
    await expect(code).toHaveText(/^[A-Z2-7]{4}(-[A-Z2-7]{1,4}){6}$/);
    await expect(code).not.toHaveText(recoveryCode());

    await page.getByRole("link", { name: /sign in/i }).click();
    await page.getByLabel("Email").fill(EMAILS.careful);
    await page.getByLabel("Password", { exact: true }).fill(RECOVERED_PASSWORD);
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page).toHaveURL(/\/today$/);
  });
});
