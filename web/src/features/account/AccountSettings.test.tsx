import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { toast } from "sonner";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { Toaster } from "@/components/ui/toast";
import { greeting } from "@/features/today/TodayScreen";
import { getSession, resetSession, signIn } from "@/lib/session";
import { fakeApi, ok, problem, token, USER, type Reply } from "@/test/fakeApi";

import { AccountSettings } from "./AccountSettings";

const LOGIN = "POST /api/auth/login";
const DEVICES = "GET /api/account/sessions";
const SAVE = "PATCH /api/account/profile";
const UNDO = "POST /api/events/e1/undo";
const ME = "GET /api/me";

const named = { ...USER, display_name: "Asha", version: 2 };

async function open(routes: Record<string, Reply[]>) {
  const server = fakeApi({
    [LOGIN]: [ok({ access_token: "t", user: USER })],
    [DEVICES]: [ok({ items: [] })],
    "POST /api/auth/refresh": [token("t2")],
    ...routes,
  });
  await signIn("you@example.com", "password");
  render(
    <QueryClientProvider client={new QueryClient()}>
      <AccountSettings />
      <Toaster />
    </QueryClientProvider>,
  );
  return server;
}

async function saveName(name: string) {
  await userEvent.type(screen.getByLabelText("Your name"), name);
  await userEvent.click(screen.getByRole("button", { name: "Save name" }));
}

const shownName = () => {
  const session = getSession();
  return session.status === "signedIn" ? session.user.display_name : "signed out";
};

beforeEach(() => {
  // The toast library asks about the system's motion setting.
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => ({ matches: true, addEventListener() {}, removeEventListener() {} })),
  );
});

afterEach(() => {
  // Messages live outside the component, so they would otherwise reach the next test.
  act(() => void toast.dismiss());
  resetSession();
  vi.unstubAllGlobals();
});

describe("account settings with the API", () => {
  it("saves the name with its version, and Undo puts it back", async () => {
    const server = await open({
      [SAVE]: [ok({ user: named, event_id: "e1" })],
      [UNDO]: [ok({ event_id: "e2" })],
      [ME]: [ok({ ...USER, version: 3 })],
    });

    await saveName("Asha");
    expect(await screen.findByText("Name saved")).toBeInTheDocument();
    expect(server.calls.find((call) => call.route === SAVE)!.body).toEqual({
      display_name: "Asha",
      version: 1,
    });
    expect(shownName()).toBe("Asha");

    fireEvent.click(screen.getByRole("button", { name: "Undo" }));

    expect(await screen.findByText("Name put back")).toBeInTheDocument();
    expect(shownName()).toBeNull();
    expect(screen.getByLabelText("Your name")).toHaveValue("");
  });

  it("explains why Undo could not happen", async () => {
    await open({
      [SAVE]: [ok({ user: named, event_id: "e1" })],
      [UNDO]: [problem(409, "undo_blocked", "It was changed again after this.")],
    });
    await saveName("Asha");

    fireEvent.click(await screen.findByRole("button", { name: "Undo" }));

    expect(await screen.findByText("It was changed again after this.")).toBeInTheDocument();
  });

  it("shows the newer name when someone else changed it first", async () => {
    await open({
      [SAVE]: [problem(409, "conflict", "This was changed somewhere else.")],
      [ME]: [ok({ ...USER, display_name: "Other", version: 4 })],
    });

    await saveName("Asha");

    expect(await screen.findByText("This was changed somewhere else.")).toBeInTheDocument();
    expect(screen.getByLabelText("Your name")).toHaveValue("Other");
  });

  it("signs this device out when asked to sign out everywhere", async () => {
    await open({ "POST /api/auth/logout-all": [{ status: 204 }] });
    await userEvent.click(screen.getByRole("button", { name: "Sign out everywhere" }));

    await act(async () => {
      await userEvent.click(screen.getAllByRole("button", { name: "Sign out everywhere" }).at(-1)!);
      await new Promise((resolve) => setTimeout(resolve, 30));
    });

    expect(getSession()).toEqual({ status: "signedOut", chosen: true });
  });

  it("greets by name only when there is one", () => {
    expect(greeting("Asha")).toBe("Good morning, Asha.");
    expect(greeting(null)).toBe("Good morning.");
  });
});
