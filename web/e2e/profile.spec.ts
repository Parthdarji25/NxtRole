import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

import { DESKTOP, open, PHONE, sideScroll, signIn } from "./helpers";
import { MEBIBYTE, resumePdf, upload } from "./resume";

const chooser = (page: Page) => page.locator('input[type="file"]');
// The framework adds an empty alert of its own, so the form's is picked by its place.
const problem = (page: Page) => page.getByRole("main").getByRole("alert");
const heading = (page: Page, name: string) => page.getByRole("heading", { name });
const press = (page: Page, name: string | RegExp) =>
  page.getByRole("button", { name }).filter({ visible: true }).click();

async function accessibleAndNotWide(page: Page, where: string) {
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    // Messages fade in and out; their colours are checked on the screens that show them.
    .exclude("[data-sonner-toaster]")
    .analyze();
  expect(
    result.violations.map((violation) => `${violation.id} ${violation.nodes[0]?.target}`),
    where,
  ).toEqual([]);
  expect(await sideScroll(page), where).toBe(0);
}

/** Uploads the resume, confirms what is hidden and waits for the facts. */
async function readResume(page: Page, where: string) {
  await chooser(page).setInputFiles(upload("resume.pdf", resumePdf()));
  await expect(heading(page, "Check what will be hidden")).toBeVisible();
  await expect(page.getByLabel("Your name")).toHaveValue("Meera Iyer");
  await expect(page.getByText("meera.iyer@example.com")).toBeVisible();
  await accessibleAndNotWide(page, `${where}: hidden details`);
  await press(page, "Hide these and read my resume");
  await expect(heading(page, "Check what was found")).toBeVisible();
}

test.describe("on a desktop", () => {
  test.use({ viewport: DESKTOP });

  test("resume to approved profile, search, rules and a second version", async ({ page }) => {
    await signIn(page, "resume-desktop");
    await open(page, "/resume");
    await expect(heading(page, "Approve your profile first")).toBeVisible();
    await page.getByRole("link", { name: "Set up your profile" }).click();

    await readResume(page, "first resume");
    // Each fact shows its words, and the invented one was left out.
    await expect(page.getByText(/Jan 2024 - Present/).first()).toBeVisible();
    await expect(page.getByText("1 suggestion was left out")).toBeVisible();
    await expect(page.getByText("Kubernetes")).toHaveCount(0);
    await accessibleAndNotWide(page, "review");
    // Nothing is approved yet.
    await expect(page.getByRole("button", { name: "Continue" }).first()).toBeDisabled();

    await press(page, "Remove Git");
    await press(page, "Approve 5 facts");
    await expect(page.getByText("Profile approved")).toBeVisible();
    await expect(page.getByText(/Profile version 1/)).toBeVisible();
    await expect(page.getByText("Skills found · 2")).toBeVisible();

    await press(page, "Continue");
    await expect(heading(page, "What are you looking for?")).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Frontend Developer", pressed: true }),
    ).toBeVisible();
    await page.getByLabel(/Minimum salary/).fill("14");
    await accessibleAndNotWide(page, "step 2");
    await press(page, "Continue");
    await expect(page).toHaveURL(/step=3/);

    await open(page, "/settings/sources");
    await expect(page.getByText("Fixed pay of ₹14 lakh a year or more")).toBeVisible();
    await expect(page.getByText("You set")).toBeVisible();
    await accessibleAndNotWide(page, "rules");

    await page.getByRole("link", { name: /^Change: Fixed pay/ }).click();
    const notice = page.getByLabel("Notice period in days");
    await notice.fill("30");
    await press(page, "Save");
    await expect(page.getByText("Search saved")).toBeVisible();
    await page.reload();
    await expect(notice).toHaveValue("30");
    await notice.fill("45");
    await press(page, "Save");
    await press(page, "Undo");
    await expect(page.getByText("Change undone")).toBeVisible();
    await expect(notice).toHaveValue("30");
    await accessibleAndNotWide(page, "search settings");

    await open(page, "/resume");
    await expect(heading(page, "Your facts are approved")).toBeVisible();

    // The same file again: nothing is stored twice, and approving makes version 2.
    await open(page, "/onboarding");
    await press(page, "Replace");
    await chooser(page).setInputFiles(upload("again.pdf", resumePdf()));
    await expect(page.getByText("You uploaded this file earlier")).toBeVisible();
    await press(page, "Hide these and read my resume");
    await expect(heading(page, "Check what was found")).toBeVisible();
    // Git was removed last time, so it counts as new now.
    await expect(page.getByText("New", { exact: true })).toBeVisible();
    await press(page, "Approve 6 facts");
    await expect(page.getByText(/Profile version 2/)).toBeVisible();
    await press(page, "Undo");
    await expect(page.getByText(/Profile version 3/)).toBeVisible();
    await expect(page.getByText("Skills found · 2")).toBeVisible();
  });

  test("files that cannot be used are explained", async ({ page }) => {
    await signIn(page, "resume-files");
    await open(page, "/onboarding");

    await chooser(page).setInputFiles(upload("notes.pdf", Buffer.from("just some text")));
    await expect(problem(page)).toContainText("Upload a PDF or a Word");

    await chooser(page).setInputFiles(upload("big.pdf", resumePdf({ padding: 5 * MEBIBYTE })));
    await expect(problem(page)).toContainText("over 5 MB");

    // Just under the limit travels through the web server to the API.
    await chooser(page).setInputFiles(
      upload("large.pdf", resumePdf({ padding: 5 * MEBIBYTE - 20_000 })),
    );
    await expect(heading(page, "Check what will be hidden")).toBeVisible();
  });
});

test.describe("on a phone", () => {
  test.use({ viewport: PHONE });

  test("resume to approved profile and both parts of step 2", async ({ page }) => {
    await signIn(page, "resume-phone");
    await open(page, "/onboarding");

    await readResume(page, "phone");
    await accessibleAndNotWide(page, "phone review");
    await press(page, "Approve 6 facts");
    await expect(page.getByText("Found in your resume")).toBeVisible();
    await press(page, "Continue");

    await expect(heading(page, "Which roles should we look for?")).toBeVisible();
    await accessibleAndNotWide(page, "phone roles");
    await press(page, "Continue");
    await expect(heading(page, "Where, and for how much?")).toBeVisible();
    await press(page, "Raise the minimum salary");
    await expect(page.getByLabel(/Minimum salary/)).toHaveValue("1");
    await accessibleAndNotWide(page, "phone pay");
    await press(page, "Continue");
    await expect(page).toHaveURL(/step=3/);
  });
});
