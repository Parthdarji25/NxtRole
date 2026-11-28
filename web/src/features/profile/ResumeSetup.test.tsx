import { fireEvent, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ok, problem, type Reply } from "@/test/fakeApi";
import { renderSignedIn, signOutAfterTest } from "@/test/signedIn";

import { ResumeSetup } from "./ResumeSetup";
import type { Fact, Profile, Reading } from "./types";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

// All invented: a test needs a person to read about.
const FILE = {
  id: "f1",
  name: "cv.pdf",
  content_type: "application/pdf",
  hidden_identity: null,
};
const SKILL: Fact = {
  fact_id: "a",
  kind: "skill",
  value: "React",
  company: null,
  dates: null,
  quote: "Skills: React",
  source: "resume",
};

const profile = (part: Partial<Profile> = {}): Profile => ({
  version: 0,
  approved: null,
  summary: null,
  suggestion: null,
  reading: null,
  ...part,
});

const reading = (part: Partial<Reading> = {}): Reading => ({
  job_id: "j1",
  file_id: "f1",
  state: "running",
  problem: null,
  code: null,
  ...part,
});

const SUGGESTED = profile({
  suggestion: {
    proposal_id: "p1",
    facts: [SKILL, { ...SKILL, fact_id: "b", value: "Git" }],
    source_file_id: "f1",
    dropped: 0,
    created_at: "2026-11-28T05:00:00Z",
  },
  reading: reading({ state: "done" }),
});

const APPROVED = profile({
  version: 1,
  approved: {
    id: "v1",
    version_no: 1,
    in_use: true,
    approved_at: "2026-11-28T05:00:00Z",
    facts: [SKILL],
    source_file_id: "f1",
  },
  summary: { experience_years: "3", latest_role: "Developer", skills: ["React"] },
});

const READY = ok({ zero_data_retention_confirmed_on: "2026-11-28", status: "normal" });
const READ = "GET /api/profile";
const APPROVE = "POST /api/proposals/p1/approve";

const open = (routes: Record<string, Reply[]>) =>
  renderSignedIn(<ResumeSetup />, {
    "GET /api/settings/privacy": [READY],
    "GET /api/files/f1": [ok(FILE)],
    "PUT /api/preferences/setup-step": [{ status: 204 }],
    ...routes,
  });

const chooser = () => screen.findByLabelText(/Upload your resume/);
const pdf = (name = "cv.pdf") => new File(["%PDF-1.4 test"], name, { type: "application/pdf" });
const press = (name: string | RegExp) => userEvent.click(screen.getByRole("button", { name }));
// Desktop and phone each have their own button; CSS shows one of them.
const continueButtons = () => screen.getAllByRole("button", { name: "Continue" });

afterEach(() => {
  signOutAfterTest();
  push.mockReset();
});

describe("onboarding step 1 with the API", () => {
  it("uploads, shows what will be hidden, then has the resume read", async () => {
    const server = await open({
      [READ]: [ok(profile()), ok(SUGGESTED)],
      "POST /api/files/uploads": [
        { status: 201, body: { file_id: "f1", upload_url: "/api/files/f1/content?token=pass" } },
      ],
      "PUT /api/files/f1/content?token=pass": [{ status: 204 }],
      "POST /api/files/f1/complete": [
        ok({
          file: FILE,
          detected: {
            name: "Asha Rao",
            emails: ["asha@example.com"],
            phones: [],
            links: [],
            addresses: [],
          },
          warnings: [],
          duplicate: false,
        }),
      ],
      "POST /api/profile/parse": [{ status: 202, body: reading() }],
    });

    await userEvent.upload(await chooser(), pdf());
    expect(await screen.findByText("Check what will be hidden")).toBeInTheDocument();
    // Nothing has gone to AI yet.
    expect(server.count("POST /api/profile/parse")).toBe(0);
    // The file goes with its one-file pass, not with the sign-in.
    const sent = server.calls.find((call) => call.route.startsWith("PUT /api/files"))!;
    expect(sent.headers).toEqual({ "Content-Type": "application/pdf" });

    await userEvent.type(screen.getByLabelText("Add words to hide"), "Secret Project{Enter}");
    await press("Hide these and read my resume");

    expect(await screen.findByText("Check what was found")).toBeInTheDocument();
    expect(server.calls.find((call) => call.route === "POST /api/profile/parse")!.body).toEqual({
      file_id: "f1",
      hide: {
        name: "Asha Rao",
        emails: ["asha@example.com"],
        phones: [],
        links: [],
        addresses: [],
        other: ["Secret Project"],
      },
    });
    for (const button of continueButtons()) expect(button).toBeDisabled();
  });

  it("explains a refused file and lets another be chosen", async () => {
    await open({
      [READ]: [ok(profile())],
      "POST /api/files/uploads": [
        problem(415, "unsupported_type", "Upload a PDF or a Word (.docx) file."),
      ],
    });

    await userEvent.upload(await chooser(), pdf());

    expect(await screen.findByRole("alert")).toHaveTextContent("Upload a PDF or a Word");
    expect(await chooser()).toBeInTheDocument();
  });

  it("does not send a file that is plainly wrong", async () => {
    const server = await open({ [READ]: [ok(profile())] });

    await userEvent.upload(await chooser(), pdf("cv.pdf.exe"), { applyAccept: false });

    expect(await screen.findByRole("alert")).toHaveTextContent("Upload a PDF or a Word");
    expect(server.count("POST /api/files/uploads")).toBe(0);
  });

  it("approves only what the owner kept, and can undo", async () => {
    const server = await open({
      [READ]: [ok(SUGGESTED), ok(APPROVED), ok(profile())],
      [APPROVE]: [ok({ proposal: {}, event_id: "e1" })],
      "POST /api/events/e1/undo": [ok({ event_id: "e2" })],
    });
    await screen.findByText("Check what was found");

    await press("Remove Git");
    await press("Approve 1 fact");

    expect(await screen.findByText("Profile approved")).toBeInTheDocument();
    expect(server.calls.find((call) => call.route === APPROVE)!.body).toEqual({
      edited_payload: { facts: [SKILL], source_file_id: "f1" },
    });
    for (const button of continueButtons()) expect(button).toBeEnabled();

    fireEvent.click(screen.getByRole("button", { name: "Undo" }));

    expect(await screen.findByText("Approval undone")).toBeInTheDocument();
    expect(await chooser()).toBeInTheDocument();
  });

  it("shows the stored profile when the suggestion was already decided", async () => {
    await open({
      [READ]: [ok(SUGGESTED), ok(APPROVED)],
      [APPROVE]: [problem(409, "conflict", "This suggestion was already decided.")],
    });
    await screen.findByText("Check what was found");

    await press(/Approve 2 facts/);

    expect(await screen.findByText(/Profile version 1/)).toBeInTheDocument();
  });

  it("saves an edit of the approved facts with the version it started from", async () => {
    const server = await open({
      [READ]: [ok(APPROVED)],
      "PUT /api/profile": [ok({ profile: APPROVED, event_id: "e1" })],
    });
    await userEvent.click(await screen.findByRole("button", { name: "Review or edit facts" }));

    await press("Add a fact");
    await userEvent.type(screen.getByLabelText("Fact"), "TypeScript");
    await press("Add");
    await press("Save changes");

    expect(await screen.findByText("Profile saved")).toBeInTheDocument();
    const body = server.calls.find((call) => call.route === "PUT /api/profile")!.body as {
      facts: Fact[];
      version: number;
    };
    expect(body.version).toBe(1);
    expect(body.facts.at(-1)).toMatchObject({ value: "TypeScript", source: "you", quote: null });
  });

  it("says when the free limit is used up, and tries again on request", async () => {
    const waiting = reading({
      state: "queued",
      code: "ai_limits_reached",
      problem: "The free AI limit is used up for now.",
    });
    const server = await open({
      [READ]: [ok(profile({ reading: waiting })), ok(SUGGESTED)],
      "POST /api/profile/parse/j1/retry": [{ status: 202, body: reading() }],
    });
    expect(await screen.findByText("The free AI limit is used up for now.")).toBeInTheDocument();
    expect(screen.getByText("Waiting for AI")).toBeInTheDocument();

    await press("Try again");

    expect(await screen.findByText("Check what was found")).toBeInTheDocument();
    expect(server.count("POST /api/profile/parse/j1/retry")).toBe(1);
  });

  it("lets a failed attempt be put aside to keep the approved profile", async () => {
    const failed = reading({
      state: "failed",
      code: "ai_bad_answer",
      problem: "No usable answer.",
    });
    await open({ [READ]: [ok({ ...APPROVED, reading: failed })] });

    await userEvent.click(await screen.findByRole("button", { name: "Keep my current profile" }));

    expect(screen.getByText(/Profile version 1/)).toBeInTheDocument();
  });

  it("says before any upload that AI is not set up", async () => {
    await open({
      [READ]: [ok(profile())],
      "GET /api/settings/privacy": [
        ok({ zero_data_retention_confirmed_on: null, status: "not_set_up" }),
      ],
    });

    expect(await screen.findByText(/the Groq key is missing/)).toBeInTheDocument();
  });

  it("shows a way to try again when the profile does not load", async () => {
    await open({ [READ]: ["offline", ok(profile())] });

    await userEvent.click(await screen.findByRole("button", { name: "Try again" }));

    expect(await chooser()).toBeInTheDocument();
  });
});
