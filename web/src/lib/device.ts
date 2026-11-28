/** Turns a browser's long self-description into words such as "Chrome on Windows". */

// The order matters: Edge and Opera also say "Chrome", and Chrome also says "Safari".
const BROWSERS: [RegExp, string][] = [
  [/Edg(e|A|iOS)?\//, "Edge"],
  [/OPR\//, "Opera"],
  [/SamsungBrowser\//, "Samsung Internet"],
  [/(Firefox|FxiOS)\//, "Firefox"],
  [/(Chrome|CriOS)\//, "Chrome"],
  [/Safari\//, "Safari"],
];

const SYSTEMS: [RegExp, string][] = [
  [/iPhone/, "iPhone"],
  [/iPad/, "iPad"],
  [/Android/, "Android"],
  [/Windows/, "Windows"],
  [/Mac OS X/, "Mac"],
  [/Linux/, "Linux"],
];

const named = (list: [RegExp, string][], text: string) =>
  list.find(([pattern]) => pattern.test(text))?.[1];

export function deviceName(userAgent: string | null): string {
  const browser = userAgent ? named(BROWSERS, userAgent) : undefined;
  const system = userAgent ? named(SYSTEMS, userAgent) : undefined;
  if (browser && system) return `${browser} on ${system}`;
  return browser ?? system ?? "Unknown device";
}
