import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/http";
import { deviceName } from "@/lib/device";
import { shortDateTime } from "@/lib/dates";

import { AccountView, type AccountActions, type Device } from "./AccountView";

const USER = { id: "u1", email: "you@example.com", display_name: null, version: 1 };
const device = (family_id: string, current: boolean): Device => ({
  family_id,
  signed_in_at: "2026-11-27T03:10:00Z",
  last_used_at: "2026-11-27T12:40:00Z",
  user_agent: "Windows NT 10.0 Chrome/140.0 Safari/537.36",
  ip_hint: null,
  current,
});

function actions(): AccountActions {
  return {
    saveName: vi.fn(async () => {}),
    changePassword: vi.fn(async () => {}),
    signOutDevice: vi.fn(async () => {}),
    signOut: vi.fn(async () => {}),
    signOutEverywhere: vi.fn(async () => {}),
  };
}

function show(
  using = actions(),
  devices: React.ComponentProps<typeof AccountView>["devices"] = {
    status: "ready",
    items: [device("here", true), device("there", false)],
  },
) {
  render(<AccountView user={USER} devices={devices} actions={using} />);
  return using;
}

const button = (name: string | RegExp) => screen.getByRole("button", { name });

describe("account settings", () => {
  it("saves a trimmed name, and only when it changed", async () => {
    const using = show();
    expect(button("Save name")).toBeDisabled();

    await userEvent.type(screen.getByLabelText("Your name"), "  Asha ");
    await userEvent.click(button("Save name"));

    expect(using.saveName).toHaveBeenCalledWith("Asha");
  });

  it("offers to sign out other devices, not this one", async () => {
    const using = show();

    expect(screen.getByText("This device")).toBeInTheDocument();
    await userEvent.click(button("Sign out Chrome on Windows"));

    expect(using.signOutDevice).toHaveBeenCalledWith("there");
  });

  it("asks before signing out everywhere", async () => {
    const using = show();

    await userEvent.click(button("Sign out everywhere"));
    expect(using.signOutEverywhere).not.toHaveBeenCalled();
    await userEvent.click(screen.getAllByRole("button", { name: "Sign out everywhere" })[0]!);

    expect(using.signOutEverywhere).toHaveBeenCalledTimes(1);
  });

  it("checks the new password before sending it", async () => {
    const using = show();
    await userEvent.click(button("Change password"));

    await userEvent.type(screen.getByLabelText("Current password"), "old password here");
    await userEvent.type(screen.getByLabelText("New password"), "short");
    await userEvent.type(screen.getByLabelText("New password again"), "different");
    await userEvent.click(screen.getByRole("button", { name: "Change password" }));

    expect(await screen.findByText(/at least 12 characters\. A short/)).toBeInTheDocument();
    expect(using.changePassword).not.toHaveBeenCalled();
  });

  it("shows the reason a change was refused and keeps the form open", async () => {
    const using = actions();
    using.changePassword = vi.fn(async () => {
      throw new ApiError(401, { code: "invalid_credentials", message: "That is not right." });
    });
    show(using);
    await userEvent.click(button("Change password"));
    await userEvent.type(screen.getByLabelText("Current password"), "old password here");
    await userEvent.type(screen.getByLabelText("New password"), "a new long password");
    await userEvent.type(screen.getByLabelText("New password again"), "a new long password");

    await userEvent.click(screen.getByRole("button", { name: "Change password" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("That is not right.");
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("has loading and error states for the device list", async () => {
    const retry = vi.fn();
    const { unmount } = render(
      <AccountView user={USER} devices={{ status: "loading" }} actions={actions()} />,
    );
    expect(screen.getByRole("status")).toHaveTextContent("Loading devices");
    unmount();

    show(actions(), { status: "error", message: "No answer.", retry });
    await userEvent.click(button("Try again"));

    expect(retry).toHaveBeenCalled();
  });
});

describe("device names and times", () => {
  it.each([
    ["Mozilla/5.0 (Windows NT 10.0) Chrome/140 Safari/537.36", "Chrome on Windows"],
    ["Mozilla/5.0 (Windows NT 10.0) Chrome/140 Safari/537.36 Edg/140", "Edge on Windows"],
    ["Mozilla/5.0 (iPhone; CPU iPhone OS) Version/26 Safari/604.1", "Safari on iPhone"],
    ["Mozilla/5.0 (Linux; Android 16) Chrome/140 Mobile Safari/537.36", "Chrome on Android"],
    ["Mozilla/5.0 (X11; Linux x86_64) Firefox/140", "Firefox on Linux"],
    ["curl/8.0", "Unknown device"],
    [null, "Unknown device"],
  ])("reads %s", (agent, name) => {
    expect(deviceName(agent)).toBe(name);
  });

  it("shows times in India Standard Time", () => {
    expect(shortDateTime(new Date("2026-11-27T20:00:00Z"))).toBe("28 Nov, 1:30 am");
  });
});
