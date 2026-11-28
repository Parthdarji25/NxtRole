import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { resetSession } from "@/lib/session";
import { fakeApi, ok, problem, token, USER } from "@/test/fakeApi";

import { RequireSignIn } from "./RequireSignIn";

const replace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
  usePathname: () => "/jobs",
}));

const protectedScreen = (
  <RequireSignIn>
    <h1>Jobs</h1>
  </RequireSignIn>
);

afterEach(() => {
  resetSession();
  replace.mockReset();
  vi.unstubAllGlobals();
});

describe("protected screens", () => {
  it("show placeholders first, then the screen to the signed-in owner", async () => {
    fakeApi({ "POST /api/auth/refresh": [token("t")], "GET /api/me": [ok(USER)] });

    render(protectedScreen);

    expect(screen.getByRole("status")).toHaveTextContent("Loading");
    expect(screen.queryByRole("heading", { name: "Jobs" })).not.toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Jobs" })).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });

  it("send a visitor to sign in and remember the screen (FR-006)", async () => {
    fakeApi({ "POST /api/auth/refresh": [problem(401, "invalid_refresh")] });

    render(protectedScreen);

    await vi.waitFor(() => expect(replace).toHaveBeenCalledWith("/login?next=%2Fjobs"));
    expect(screen.queryByRole("heading", { name: "Jobs" })).not.toBeInTheDocument();
  });

  it("offer to try again when the API cannot be reached", async () => {
    fakeApi({ "POST /api/auth/refresh": ["offline", token("t")], "GET /api/me": [ok(USER)] });
    render(protectedScreen);

    await userEvent.click(await screen.findByRole("button", { name: /try again|retry/i }));

    expect(await screen.findByRole("heading", { name: "Jobs" })).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });
});
