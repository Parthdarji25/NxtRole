/**
 * Resume files for the browser tests, made from the synthetic resume the API tests use (an
 * invented person).
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const TEXT = readFileSync(
  fileURLToPath(
    new URL("../../api/tests/fixtures/resume_synthetic_2026-11-28.txt", import.meta.url),
  ),
  "utf-8",
)
  .replaceAll("\r\n", "\n")
  .trim();

export const MEBIBYTE = 1024 * 1024;

/**
 * A one-page PDF holding the resume. `padding` adds that many bytes of a comment, which
 * readers skip, to make a large file.
 */
export function resumePdf({ padding = 0 } = {}): Buffer {
  const commands = ["BT", "/F1 10 Tf", "40 800 Td"];
  for (const line of TEXT.split("\n")) {
    commands.push(`(${line.replace(/[\\()]/g, "\\$&")}) Tj`, "0 -13 Td");
  }
  const stream = [...commands, "ET"].join("\n");
  const objects = [
    "<< /Type /Catalog /Pages 2 0 R >>",
    "<< /Type /Pages /Kids [4 0 R] /Count 1 >>",
    "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] " +
      "/Resources << /Font << /F1 3 0 R >> >> /Contents 5 0 R >>",
    `<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`,
  ];

  let out = "%PDF-1.4\n";
  if (padding > 0) out += `%${"x".repeat(padding)}\n`;
  const offsets: number[] = [];
  objects.forEach((body, index) => {
    offsets.push(out.length);
    out += `${index + 1} 0 obj\n${body}\nendobj\n`;
  });
  const table = out.length;
  out += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  for (const offset of offsets) out += `${String(offset).padStart(10, "0")} 00000 n \n`;
  out += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${table}\n%%EOF\n`;
  // Only Latin letters, so one character is one byte.
  return Buffer.from(out, "latin1");
}

export const upload = (name: string, buffer: Buffer) => ({
  name,
  mimeType: "application/pdf",
  buffer,
});
