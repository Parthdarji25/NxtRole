import { describe, expect, it } from "vitest";

import { buildContentSecurityPolicy } from "./csp";

const build = (isDevelopment: boolean, isHttps: boolean) =>
  buildContentSecurityPolicy({ nonce: "abc123", isDevelopment, isHttps });

describe("content security policy", () => {
  it("only lets scripts with this request's nonce run", () => {
    const scripts = build(false, true)
      .split("; ")
      .find((part) => part.startsWith("script-src"));
    expect(scripts).toBe("script-src 'self' 'nonce-abc123' 'strict-dynamic'");
  });

  it("allows eval in development only", () => {
    expect(build(true, false)).toContain("'unsafe-eval'");
    expect(build(false, false)).not.toContain("'unsafe-eval'");
  });

  it("forbids framing, plugins and outside connections", () => {
    const policy = build(false, false);
    expect(policy).toContain("frame-ancestors 'none'");
    expect(policy).toContain("object-src 'none'");
    expect(policy).toContain("connect-src 'self'");
  });

  it("upgrades insecure requests on HTTPS only", () => {
    expect(build(false, true)).toContain("upgrade-insecure-requests");
    expect(build(false, false)).not.toContain("upgrade-insecure-requests");
  });
});
