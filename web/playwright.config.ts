import { randomBytes } from "node:crypto";

import { defineConfig, devices } from "@playwright/test";

import { EMAILS } from "./e2e/accounts";

const isCI = Boolean(process.env.CI);
// The tests use their own ports, so development servers on 3000 and 8000 can keep running.
const WEB = "http://127.0.0.1:3100";
const API = "http://127.0.0.1:8100";

// A new password and recovery code for every run. The test processes inherit them.
process.env.E2E_PASSWORD ??= `pw ${randomBytes(18).toString("base64url")}`;
process.env.E2E_RECOVERY_CODE ??= Array.from(randomBytes(26), (byte) =>
  "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567".charAt(byte % 32),
).join("");

// Browser tests build the web app and start it with an API on a throw-away database
// (api/tests/e2e_server.py). The database and Redis containers must be running first.
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  workers: isCI ? 2 : 3,
  forbidOnly: isCI,
  retries: isCI ? 1 : 0,
  reporter: isCI ? [["list"], ["html", { open: "never" }]] : "list",
  // Approved pictures live next to the visual tests.
  snapshotPathTemplate: "{testDir}/visual/pictures/{arg}-{platform}{ext}",
  use: {
    baseURL: WEB,
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "uv run python -m tests.e2e_server",
      cwd: "../api",
      url: `${API}/health`,
      env: { E2E_EMAILS: JSON.stringify(Object.values(EMAILS)) },
      // Always a new one: it builds the database the tests expect.
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      // The production build: what actually ships.
      command: "pnpm build && pnpm exec next start --hostname 127.0.0.1 --port 3100",
      url: WEB,
      env: { API_URL: API },
      reuseExistingServer: false,
      timeout: 300_000,
    },
  ],
});
