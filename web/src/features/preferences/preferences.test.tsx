import { fireEvent, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PrivacyContainer } from "@/features/privacy/PrivacyContainer";
import { RequireProfile } from "@/features/profile/RequireProfile";
import { RulesContainer } from "@/features/rules/RulesContainer";
import { ok, problem, type Reply } from "@/test/fakeApi";
import { renderSignedIn, signOutAfterTest } from "@/test/signedIn";

import type { Preferences } from "./draft";
import { PreferencesSetup } from "./PreferencesSetup";
import { SearchSettingsContainer } from "./SearchSettingsContainer";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

const preferences = (part: Partial<Preferences> = {}): Preferences => ({
  titles: [],
  places: [],
  experience_min: null,
  experience_max: null,
  notice_days: null,
  expected_ctc_lpa: null,
  min_salary_lpa: null,
  work_modes: ["remote", "hybrid", "onsite"],
  avoid_company_types: [],
  version: 0,
  onboarding_step: 1,
  ...part,
});

const NO_PROFILE = { version: 0, approved: null, summary: null, suggestion: null, reading: null };

// Invented facts: a test needs something to suggest from.
const PROFILE = {
  ...NO_PROFILE,
  version: 1,
  approved: {
    facts: [
      { fact_id: "r", kind: "role", value: "Developer" },
      { fact_id: "l", kind: "location", value: "Pune, Maharashtra" },
    ],
  },
  summary: { experience_years: "3", latest_role: "Developer", skills: [] },
};

const READ = "GET /api/preferences";
const SAVE = "PUT /api/preferences";

const open = (screenToShow: React.ReactNode, routes: Record<string, Reply[]>) =>
  renderSignedIn(screenToShow, {
    "GET /api/profile": [ok(PROFILE)],
    "PUT /api/preferences/setup-step": [{ status: 204 }],
    ...routes,
  });

const bodyOf = (server: Awaited<ReturnType<typeof open>>) =>
  server.calls.find((call) => call.route === SAVE)!.body;

afterEach(() => {
  signOutAfterTest();
  push.mockReset();
});

describe("onboarding step 2 with the API", () => {
  it("fills in the role and city from the profile, and saves them", async () => {
    const server = await open(<PreferencesSetup />, {
      [READ]: [ok(preferences())],
      [SAVE]: [ok({ preferences: preferences({ version: 1 }), event_id: "e1" })],
    });
    await screen.findByRole("button", { name: /Developer/, pressed: true });
    expect(screen.getByRole("button", { name: "Remote (India)" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );

    await userEvent.type(screen.getByLabelText(/Minimum salary/), "14");
    // The desktop button is the first one.
    await userEvent.click(screen.getAllByRole("button", { name: "Continue" })[0]!);

    await vi.waitFor(() => expect(push).toHaveBeenCalledWith("/onboarding?step=3"));
    expect(bodyOf(server)).toMatchObject({
      titles: ["Developer"],
      places: ["Pune"],
      min_salary_lpa: "14",
      version: 0,
    });
  });

  it("keeps the owner here when the salary cannot be read", async () => {
    const server = await open(<PreferencesSetup />, { [READ]: [ok(preferences())] });
    await screen.findByRole("button", { name: /Developer/, pressed: true });

    await userEvent.type(screen.getByLabelText(/Minimum salary/), "lots");
    await userEvent.click(screen.getAllByRole("button", { name: "Continue" })[0]!);

    expect(await screen.findByRole("alert")).toHaveTextContent("Enter lakhs a year");
    expect(server.count(SAVE)).toBe(0);
    expect(push).not.toHaveBeenCalled();
  });
});

describe("Settings > Search with the API", () => {
  const saved = preferences({ titles: ["Developer"], min_salary_lpa: "14", version: 2 });

  it("saves a change with its version, and Undo reads the old values again", async () => {
    const server = await open(<SearchSettingsContainer />, {
      [READ]: [ok(saved), ok({ ...saved, version: 4 })],
      [SAVE]: [ok({ preferences: { ...saved, notice_days: 30, version: 3 }, event_id: "e1" })],
      "POST /api/events/e1/undo": [ok({ event_id: "e2" })],
    });
    const save = await screen.findByRole("button", { name: "Save" });
    expect(save).toBeDisabled();

    await userEvent.type(screen.getByLabelText("Notice period in days"), "30");
    await userEvent.click(save);

    expect(await screen.findByText("Search saved")).toBeInTheDocument();
    expect(bodyOf(server)).toMatchObject({ notice_days: 30, version: 2 });
    expect(screen.getByLabelText("Notice period in days")).toHaveValue("30");

    fireEvent.click(screen.getByRole("button", { name: "Undo" }));

    expect(await screen.findByText("Change undone")).toBeInTheDocument();
    await vi.waitFor(() => expect(screen.getByLabelText("Notice period in days")).toHaveValue(""));
  });

  it("shows what is stored when it was changed elsewhere", async () => {
    await open(<SearchSettingsContainer />, {
      [READ]: [ok(saved), ok({ ...saved, titles: ["Designer"], version: 5 })],
      [SAVE]: [problem(409, "conflict", "This was changed elsewhere.")],
    });
    await userEvent.type(await screen.findByLabelText("Notice period in days"), "30");

    await userEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByText("Designer")).toBeInTheDocument();
  });

  it("asks for the profile before showing experience from the resume", async () => {
    await open(<SearchSettingsContainer />, {
      [READ]: [ok(saved)],
      "GET /api/profile": [ok(NO_PROFILE)],
    });

    const row = await screen.findByRole("group", { name: "Experience" });

    expect(within(row).getByRole("link", { name: "Approve your profile first" })).toHaveAttribute(
      "href",
      "/onboarding",
    );
  });
});

describe("privacy, rules and the profile gate", () => {
  it("shows the confirmed date", async () => {
    await open(<PrivacyContainer />, {
      "GET /api/settings/privacy": [
        ok({ zero_data_retention_confirmed_on: "2026-11-28", status: "normal" }),
      ],
    });

    expect(await screen.findByText("Confirmed 28 Nov 2026")).toBeInTheDocument();
    expect(screen.queryByRole("switch")).not.toBeInTheDocument();
  });

  it("says that AI is paused until it is confirmed", async () => {
    await open(<PrivacyContainer />, {
      "GET /api/settings/privacy": [
        ok({ zero_data_retention_confirmed_on: null, status: "privacy_not_confirmed" }),
      ],
    });

    expect(await screen.findByText("Not confirmed")).toBeInTheDocument();
    expect(screen.getByText("AI paused")).toBeInTheDocument();
  });

  it("lists the owner's rules", async () => {
    await open(<RulesContainer />, {
      "GET /api/rules": [
        ok({
          items: [
            {
              id: "1",
              kind: "min_fixed_pay",
              text: "Fixed pay of ₹14 lakh a year or more",
              origin: "you",
              status: "active",
              hid_count: 0,
            },
          ],
        }),
      ],
    });

    expect(await screen.findByText("You set")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /^Change: Fixed pay/ })).toHaveAttribute(
      "href",
      "/settings?section=search",
    );
  });

  it("says how to make the first rule", async () => {
    await open(<RulesContainer />, { "GET /api/rules": [ok({ items: [] })] });

    expect(await screen.findByText(/No rules yet/)).toBeInTheDocument();
  });

  it.each([
    ["without approved facts", NO_PROFILE, "Approve your profile first"],
    ["with approved facts", PROFILE, "Inside"],
  ])("the profile gate %s", async (_name, found, text) => {
    await open(
      <RequireProfile>
        <p>Inside</p>
      </RequireProfile>,
      { "GET /api/profile": [ok(found)] },
    );

    expect(await screen.findByText(text)).toBeInTheDocument();
  });
});
