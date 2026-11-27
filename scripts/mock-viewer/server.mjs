// Development tool only (D-046): shows the design mocks in a browser.
//   node scripts/mock-viewer/server.mjs        then open http://127.0.0.1:4173
import { readFile } from "node:fs/promises";
import { createServer } from "node:http";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = fileURLToPath(new URL(".", import.meta.url));
export const mockDir = fileURLToPath(new URL("../../docs/mocks/source/", import.meta.url));

export async function readBoards() {
  const canvas = JSON.parse(await readFile(`${mockDir}canvas.json`, "utf8"));
  return canvas.order.map((file) => ({ file, ...canvas.boards[file] }));
}

async function indexPage() {
  const boards = await readBoards();
  const rows = boards
    .map((b) => `<li><a href="/${b.file}">${b.file}</a> (${b.w} × ${b.h})</li>`)
    .join("");
  return `<!doctype html><meta charset="utf-8"><title>NxtRole mocks</title>
<body style="font-family:system-ui;padding:24px"><h1>NxtRole mocks</h1>
<p>Dark theme: run <code>localStorage.setItem("morrow-theme","dark")</code> in the browser console.</p>
<ul>${rows}</ul>`;
}

export function startServer(port = 4173) {
  const server = createServer(async (request, response) => {
    const path = new URL(request.url, "http://localhost").pathname;
    const send = (status, type, body) => {
      response.writeHead(status, { "Content-Type": `${type}; charset=utf-8` });
      response.end(body);
    };
    try {
      if (path === "/") return send(200, "text/html", await indexPage());
      if (path === "/support.js") {
        return send(200, "text/javascript", await readFile(`${here}support.js`));
      }
      // Only mock files directly inside the mock folder can be read.
      const name = decodeURIComponent(path.slice(1));
      if (/^[A-Za-z0-9]+\.dc\.html$/.test(name)) {
        return send(200, "text/html", await readFile(`${mockDir}${name}`));
      }
      return send(404, "text/plain", "Not found");
    } catch {
      return send(404, "text/plain", "Not found");
    }
  });
  return new Promise((resolve) => server.listen(port, "127.0.0.1", () => resolve(server)));
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  await startServer();
  console.log("Mocks: http://127.0.0.1:4173  (Ctrl+C to stop)");
}
