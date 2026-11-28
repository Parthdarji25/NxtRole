import { afterEach, describe, expect, it, vi } from "vitest";

import { fakeApi, ok, problem, token, USER } from "@/test/fakeApi";

import { api, ApiError } from "./api";
import { getSession, resetSession, restore, signIn, signOut } from "./session";

const REFRESH = "POST /api/auth/refresh";
const ME = "GET /api/me";
const DATA = "GET /api/data";
const LOGIN = "POST /api/auth/login";
const LOGOUT = "POST /api/auth/logout";

const signedInReply = ok({ access_token: "first", user: USER });

afterEach(() => {
  resetSession();
  vi.unstubAllGlobals();
});

describe("calling the API", () => {
  it("@E-56 refreshes once for many expired requests, then retries each", async () => {
    const server = fakeApi({
      [LOGIN]: [signedInReply],
      [DATA]: [
        problem(401, "token_expired"),
        problem(401, "token_expired"),
        problem(401, "token_expired"),
        ok({ value: 1 }),
      ],
      [REFRESH]: [token("second")],
    });
    await signIn("you@example.com", "password");

    const answers = await Promise.all([1, 2, 3].map(() => api<{ value: number }>("/api/data")));

    expect(answers).toEqual([{ value: 1 }, { value: 1 }, { value: 1 }]);
    expect(server.count(REFRESH)).toBe(1);
    expect(server.count(DATA)).toBe(6);
    expect(server.calls.at(-1)!.headers.Authorization).toBe("Bearer second");
    expect(server.calls.find((call) => call.route === REFRESH)!.headers).toEqual({
      "X-NxtRole-CSRF": "1",
    });
  });

  it("retries only once", async () => {
    const server = fakeApi({
      [LOGIN]: [signedInReply],
      [DATA]: [problem(401, "token_expired")],
      [REFRESH]: [token("second")],
    });
    await signIn("you@example.com", "password");

    await expect(api("/api/data")).rejects.toMatchObject({ code: "token_expired" });
    expect(server.count(DATA)).toBe(2);
  });

  it("shows signed out when the sign-in can no longer be refreshed", async () => {
    fakeApi({
      [LOGIN]: [signedInReply],
      [DATA]: [problem(401, "token_expired")],
      [REFRESH]: [problem(401, "session_reused")],
    });
    await signIn("you@example.com", "password");

    await expect(api("/api/data")).rejects.toBeInstanceOf(ApiError);
    expect(getSession()).toEqual({ status: "signedOut", chosen: false });
  });

  it("shows signed out when this device was signed out elsewhere", async () => {
    fakeApi({ [LOGIN]: [signedInReply], [DATA]: [problem(401, "unauthorized")] });
    await signIn("you@example.com", "password");

    await expect(api("/api/data")).rejects.toMatchObject({ code: "unauthorized" });
    expect(getSession().status).toBe("signedOut");
  });

  it("stays signed in when a request is refused for another reason", async () => {
    fakeApi({ [LOGIN]: [signedInReply], [DATA]: [problem(401, "invalid_credentials")] });
    await signIn("you@example.com", "password");

    await expect(api("/api/data")).rejects.toMatchObject({ code: "invalid_credentials" });
    expect(getSession().status).toBe("signedIn");
  });

  it.each([
    ["the network is down", "offline" as const],
    ["the forwarding server answers with a web page", { status: 500, body: "<html>" }],
  ])("explains when %s", async (_case, reply) => {
    fakeApi({ [LOGIN]: [signedInReply], [DATA]: [reply] });
    await signIn("you@example.com", "password");

    await expect(api("/api/data")).rejects.toMatchObject({
      code: "unreachable",
      message: expect.stringContaining("cannot be reached"),
    });
    expect(getSession().status).toBe("signedIn");
  });
});

describe("signing in and out", () => {
  it("restores a sign-in from the cookie when a screen opens", async () => {
    const server = fakeApi({ [REFRESH]: [token("first")], [ME]: [ok(USER)] });

    await Promise.all([restore(), restore()]);

    expect(getSession()).toEqual({ status: "signedIn", user: USER });
    expect(server.count(REFRESH)).toBe(1);
  });

  it("is signed out without a cookie", async () => {
    fakeApi({ [REFRESH]: [problem(401, "invalid_refresh")] });

    await restore();

    expect(getSession()).toEqual({ status: "signedOut", chosen: false });
  });

  it("does not sign out when the API cannot be reached", async () => {
    fakeApi({ [REFRESH]: ["offline", token("first")], [ME]: [ok(USER)] });

    await restore();
    expect(getSession().status).toBe("unreachable");
    await restore();

    expect(getSession().status).toBe("signedIn");
  });

  it("never stores the token where other code could read it later", async () => {
    fakeApi({ [LOGIN]: [signedInReply] });

    await signIn("you@example.com", "password");

    const stored = JSON.stringify([{ ...localStorage }, { ...sessionStorage }, document.cookie]);
    expect(stored).not.toContain("first");
  });

  it("signs out, and tells the other tabs", async () => {
    fakeApi({ [LOGIN]: [signedInReply], [LOGOUT]: [{ status: 204 }] });
    const otherTab = new BroadcastChannel("nxtrole-auth");
    const heard: unknown[] = [];
    otherTab.onmessage = (event) => heard.push(event.data);
    await signIn("you@example.com", "password");

    await signOut();

    expect(getSession()).toEqual({ status: "signedOut", chosen: true });
    await vi.waitFor(() => expect(heard).toContainEqual({ type: "signed-out", chosen: true }));
    otherTab.close();
  });

  it("follows another tab that signed out", async () => {
    fakeApi({ [REFRESH]: [token("first")], [ME]: [ok(USER)] });
    await restore();
    const otherTab = new BroadcastChannel("nxtrole-auth");

    otherTab.postMessage({ type: "signed-out", chosen: true });

    await vi.waitFor(() => expect(getSession().status).toBe("signedOut"));
    otherTab.close();
  });

  it("stays signed in if signing out cannot reach the API", async () => {
    fakeApi({ [LOGIN]: [signedInReply], [LOGOUT]: ["offline"] });
    await signIn("you@example.com", "password");

    await expect(signOut()).rejects.toMatchObject({ code: "unreachable" });
    expect(getSession().status).toBe("signedIn");
  });
});
