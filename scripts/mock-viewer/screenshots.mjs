// Development tool only (D-046): saves a picture of every mock in light and dark.
//   node scripts/mock-viewer/screenshots.mjs            all mocks
//   node scripts/mock-viewer/screenshots.mjs Nav Brief  only these
// Pictures go to docs/visual-review/mocks/ (generated files, not committed).
import { mkdir } from "node:fs/promises";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

import { readBoards, startServer } from "./server.mjs";

// Playwright is installed in the web app; reuse it instead of installing it twice.
const requireFromWeb = createRequire(new URL("../../web/package.json", import.meta.url));
const { chromium } = requireFromWeb("@playwright/test");

const outDir = fileURLToPath(new URL("../../docs/visual-review/mocks/", import.meta.url));
const wanted = process.argv.slice(2);
const port = 4174;

await mkdir(outDir, { recursive: true });
const server = await startServer(port);
const browser = await chromium.launch();
const problems = [];
let saved = 0;

try {
  const boards = (await readBoards()).filter(
    (b) => wanted.length === 0 || wanted.includes(b.file.replace(".dc.html", "")),
  );
  for (const board of boards) {
    const name = board.file.replace(".dc.html", "");
    for (const theme of ["light", "dark"]) {
      const context = await browser.newContext({
        viewport: { width: board.w, height: board.h },
        colorScheme: theme,
        reducedMotion: "reduce",
      });
      await context.addInitScript((value) => {
        window.localStorage.setItem("morrow-theme", value);
        window.localStorage.setItem("nxtrole-theme", value);
      }, theme);
      const page = await context.newPage();
      await page.goto(`http://127.0.0.1:${port}/${board.file}`, { waitUntil: "load" });
      await page.waitForFunction(() => window.__mockReady === true, undefined, { timeout: 15000 });
      await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
      await page.evaluate(() => document.fonts.ready);
      await page.waitForTimeout(600);
      const errors = await page.evaluate(() => window.__mockErrors);
      const leftovers = await page.evaluate(() => (document.body.innerText.match(/\{\{/g) ?? []).length);
      if (errors.length || leftovers) {
        problems.push(`${name} (${theme}): ${errors[0] ?? `${leftovers} unfilled bindings`}`);
      }
      await page.screenshot({ path: `${outDir}${name}-${theme}.png` });
      saved += 1;
      await context.close();
    }
  }
} finally {
  await browser.close();
  server.close();
}

console.log(`saved ${saved} pictures to docs/visual-review/mocks/`);
console.log(problems.length ? `problems:\n${problems.join("\n")}` : "no rendering errors");
process.exitCode = problems.length ? 1 : 0;
