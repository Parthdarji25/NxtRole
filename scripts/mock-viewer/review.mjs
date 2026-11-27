// Development tool only (D-046): one page with every mock beside the app's own picture.
//   node scripts/mock-viewer/screenshots.mjs     pictures of the mocks
//   (in web/) pnpm e2e:update-pictures           pictures of the app
//   node scripts/mock-viewer/review.mjs          builds docs/visual-review/index.html
import { existsSync } from "node:fs";
import { mkdir, readFile, writeFile } from "node:fs/promises";

const root = new URL("../../", import.meta.url);
const outDir = new URL("docs/visual-review/", root);
const routes = JSON.parse(await readFile(new URL("web/e2e/routes.json", root), "utf8"));
const missing = [];

/** An <img> tag, or a note when there is no picture. Paths are relative to the review page. */
function picture(path, label) {
  const found = path && existsSync(new URL(path, outDir));
  if (path && !found) missing.push(path);
  const body = found
    ? `<img src="${path}" alt="${label}" loading="lazy">`
    : `<p>${path ? "Picture not made yet." : "There is no mock for this screen."}</p>`;
  return `<figure><figcaption>${label}</figcaption>${body}</figure>`;
}

const sections = routes.map((route) => {
  const blocks = ["desktop", "phone"].flatMap((device) =>
    ["light", "dark"].map((theme) => {
      const mock = device === "desktop" ? route.desktopMock : route.phoneMock;
      return `<div class="pair ${device}" data-device="${device}" data-theme="${theme}">
        ${picture(mock && `mocks/${mock}-${theme}.png`, `Mock ${mock ?? ""}`)}
        ${picture(`../../web/e2e/visual/pictures/${route.name}-${device}-${theme}-win32.png`, `App ${route.path}`)}
      </div>`;
    }),
  );
  return `<section id="${route.name}"><h2>${route.name} <small>${route.path}</small></h2>${blocks.join("")}</section>`;
});

const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NxtRole visual review</title>
<style>
  body { margin: 0; padding: 0 20px 40px; font: 15px/1.5 system-ui, sans-serif; background: #ddd; color: #111; }
  header { position: sticky; top: 0; background: #ddd; padding: 12px 0; border-bottom: 1px solid #999; }
  nav a { margin-right: 10px; display: inline-block; }
  label { margin-right: 16px; }
  select { font: inherit; min-height: 36px; }
  .pair { display: none; gap: 16px; align-items: flex-start; }
  .pair.shown { display: flex; }
  figure { margin: 0; flex: 1 1 0; min-width: 0; }
  .phone figure { flex: 0 1 390px; }
  figcaption { font-weight: 600; padding: 4px 0; }
  img { width: 100%; display: block; border: 1px solid #888; }
</style>
</head>
<body>
<header>
  <label>Screen size <select id="device"><option value="desktop">Desktop</option><option value="phone">Phone</option></select></label>
  <label>Theme <select id="theme"><option value="light">Light</option><option value="dark">Dark</option></select></label>
  <nav>${routes.map((route) => `<a href="#${route.name}">${route.name}</a>`).join("")}</nav>
</header>
${sections.join("\n")}
<script>
  const device = document.getElementById("device");
  const theme = document.getElementById("theme");
  function show() {
    for (const pair of document.querySelectorAll(".pair")) {
      pair.classList.toggle("shown", pair.dataset.device === device.value && pair.dataset.theme === theme.value);
    }
  }
  device.addEventListener("change", show);
  theme.addEventListener("change", show);
  show();
</script>
</body>
</html>
`;

await mkdir(outDir, { recursive: true });
await writeFile(new URL("index.html", outDir), html);
console.log(`wrote docs/visual-review/index.html for ${routes.length} screens`);
console.log(missing.length ? `missing pictures:\n${missing.join("\n")}` : "no missing pictures");
process.exitCode = missing.length ? 1 : 0;
