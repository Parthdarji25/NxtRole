/**
 * Quick checks before uploading, so that an obvious mistake is told at once. The API checks
 * the contents again: only its answer counts.
 */

export const PDF = "application/pdf";
export const DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
export const MAX_BYTES = 5 * 1024 * 1024;

/** For the file chooser. */
export const ACCEPT = `.pdf,.docx,${PDF},${DOCX}`;

/** Decided by the ending of the name: browsers do not always say what a Word file is. */
export function contentTypeOf(name: string): typeof PDF | typeof DOCX | null {
  const lower = name.toLowerCase();
  if (lower.endsWith(".pdf")) return PDF;
  if (lower.endsWith(".docx")) return DOCX;
  return null;
}

export function problemWith(file: { name: string; size: number }): string | null {
  if (!contentTypeOf(file.name)) return "Upload a PDF or a Word (.docx) file.";
  if (file.size === 0) return "That file is empty.";
  if (file.size > MAX_BYTES) return "That file is over 5 MB.";
  return null;
}
