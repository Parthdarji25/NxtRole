import type { NextConfig } from "next";

/**
 * Where the API runs. Required: there is no silent default, so a wrong setup fails loudly.
 * Next.js reads web/.env.local before this file runs.
 */
function apiUrl(): string {
  const value = process.env.API_URL;
  if (!value) {
    throw new Error(
      "API_URL is missing. Copy web/.env.example to web/.env.local and fill it in " +
        "(or run scripts/new-local-env.ps1).",
    );
  }
  if (!/^https?:\/\//.test(value)) {
    throw new Error("API_URL is invalid: it must start with http:// or https://");
  }
  return value.replace(/\/+$/, "");
}

// Basic headers for every page. The stricter content security policy with a nonce
// arrives in Phase 3 (D-043, docs/SECURITY.md).
const securityHeaders = [
  {
    key: "Content-Security-Policy",
    value: "base-uri 'self'; frame-ancestors 'none'; object-src 'none'; form-action 'self'",
  },
  { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
];

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Do not announce which framework serves the pages.
  poweredByHeader: false,
  // The dev server is opened as 127.0.0.1 (scripts and tests) or localhost (browser).
  allowedDevOrigins: ["127.0.0.1", "localhost"],
  async rewrites() {
    // The browser only ever talks to this site; /api/* is forwarded to the API.
    return [{ source: "/api/:path*", destination: `${apiUrl()}/api/:path*` }];
  },
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;
