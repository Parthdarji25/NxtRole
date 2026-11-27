import { defineConfig, devices } from "@playwright/test";

const isCI = Boolean(process.env.CI);
// The tests use their own port, so a development server on 3000 can keep running.
const WEB = "http://127.0.0.1:3100";

// Browser tests build the web app and start it with the API.
// The database and Redis must be running first.
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
      command: "uv run python -m app.serve",
      cwd: "../api",
      url: "http://127.0.0.1:8000/health",
      reuseExistingServer: !isCI,
      timeout: 120_000,
    },
    {
      // The production build: what actually ships.
      command: "pnpm build && pnpm exec next start --hostname 127.0.0.1 --port 3100",
      url: WEB,
      reuseExistingServer: false,
      timeout: 300_000,
    },
  ],
});
