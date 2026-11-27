// @vitest-environment node
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

// Tests run from the web/ folder.
const read = (path: string) => readFileSync(resolve(path), "utf8").replace(/\r\n/g, "\n");
const tokens = read("src/styles/tokens.css");

/** The colours defined between a selector and its closing brace. */
function palette(selector: string): Map<string, string> {
  const start = tokens.indexOf(`${selector} {`);
  const block = tokens.slice(start, tokens.indexOf("}", start));
  return new Map(
    [...block.matchAll(/--([a-z0-9-]+):\s*(#[0-9a-f]{6})/gi)].map((match) => [
      match[1]!,
      match[2]!,
    ]),
  );
}

/** How bright a colour looks, as defined by the accessibility guidelines (WCAG). */
function luminance(hex: string): number {
  const [red, green, blue] = [1, 3, 5].map((at) => {
    const channel = parseInt(hex.slice(at, at + 2), 16) / 255;
    return channel <= 0.03928 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * red! + 0.7152 * green! + 0.0722 * blue!;
}

function contrast(a: string, b: string): number {
  const [light, dark] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (light! + 0.05) / (dark! + 0.05);
}

// Every colour pair the app uses for text: [text, background].
const PAIRS: [string, string][] = [
  ...["ink", "ink-2", "ink-3", "blue"].flatMap((text): [string, string][] => [
    [text, "paper"],
    [text, "paper-2"],
    [text, "card"],
  ]),
  ["red", "paper"],
  ["red", "card"],
  ["red-ink", "red-soft"],
  ["green", "green-soft"],
  ["amber", "amber-soft"],
  ["blue-ink", "blue-soft"],
  ["on-blue", "blue"],
  ["paper", "ink"],
];

describe("design tokens", () => {
  it("are the same as the mocks' token file", () => {
    expect(tokens).toBe(read("../docs/mocks/design-tokens.css"));
  });

  describe.each([
    ["light", ":root"],
    ["dark", '[data-theme="dark"]'],
  ])("%s theme", (_theme, selector) => {
    const colours = palette(selector);

    it.each(PAIRS)("@E-51 %s on %s is readable (4.5:1)", (text, background) => {
      const foreground = colours.get(text);
      const behind = colours.get(background);
      expect(foreground, text).toBeDefined();
      expect(behind, background).toBeDefined();
      expect(contrast(foreground!, behind!)).toBeGreaterThanOrEqual(4.5);
    });
  });
});
