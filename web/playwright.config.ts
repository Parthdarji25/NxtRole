import { defineConfig, devices } from "@playwright/test";

const isCI = Boolean(process.env.CI);

// Browser tests start the API and the web app themselves (or reuse them if already running).
// The database and Redis must be running first.
export default defineConfig({
  testDir: "./e2e",
  forbidOnly: isCI,
  retries: isCI ? 1 : 0,
  reporter: isCI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "uv run python -m app.serve",
      cwd: "../api",
      url: "http://127.0.0.1:8000/health",
      reuseExistingServer: !isCI,
      timeout: 120_000,
    },
    {
      // CI tests the production build (created by the earlier "pnpm build" step).
      command: isCI ? "pnpm start" : "pnpm dev",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: !isCI,
      timeout: 120_000,
    },
  ],
});
