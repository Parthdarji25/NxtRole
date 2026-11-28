import { describe, expect, it } from "vitest";

import { loginHref, safeNext } from "./safeNext";

describe("where to go after signing in", () => {
  it.each(["/jobs", "/settings?section=accounts", "/pipeline/offers/abc"])(
    "keeps a screen of this site: %s",
    (path) => {
      expect(safeNext(path)).toBe(path);
    },
  );

  it.each([
    undefined,
    ["/jobs", "/ask"],
    "",
    "jobs",
    "https://evil.example",
    "//evil.example",
    "/\\evil.example",
    "/a\\b",
    "/\t/evil.example",
    "javascript:alert(1)",
    "/login",
    "/login?next=/jobs",
    "/login/recover",
    `/${"a".repeat(600)}`,
  ])("goes to Today instead of %j", (value) => {
    expect(safeNext(value)).toBe("/today");
  });

  it("writes the address that returns to a screen", () => {
    expect(loginHref("/today")).toBe("/login");
    expect(loginHref("/settings?section=accounts")).toBe(
      "/login?next=%2Fsettings%3Fsection%3Daccounts",
    );
  });
});
