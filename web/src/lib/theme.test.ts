import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { chooseTheme, storedTheme, subscribeToTheme, THEME_KEY, THEME_SCRIPT } from "./theme";

type Listener = () => void;

/** Pretends to be the browser's "prefers dark" setting. */
function fakeSystem(dark: boolean) {
  const listeners = new Set<Listener>();
  const media = {
    matches: dark,
    addEventListener: (_type: string, listener: Listener) => listeners.add(listener),
    removeEventListener: (_type: string, listener: Listener) => listeners.delete(listener),
  };
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => media),
  );
  return {
    change(next: boolean) {
      media.matches = next;
      listeners.forEach((listener) => listener());
    },
  };
}

const theme = () => document.documentElement.getAttribute("data-theme");
// The same fixed script that the page runs before painting.
const runThemeScript = () => new Function(THEME_SCRIPT)();

describe("theme", () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("follows a dark system on the first visit", () => {
    fakeSystem(true);
    runThemeScript();
    expect(theme()).toBe("dark");
  });

  it("follows a light system on the first visit", () => {
    fakeSystem(false);
    runThemeScript();
    expect(theme()).toBe("light");
  });

  it("prefers the saved choice over the system", () => {
    fakeSystem(true);
    window.localStorage.setItem(THEME_KEY, "light");
    runThemeScript();
    expect(theme()).toBe("light");
  });

  it("ignores a saved value that is not a theme", () => {
    fakeSystem(true);
    window.localStorage.setItem(THEME_KEY, "<script>");
    runThemeScript();
    expect(theme()).toBe("dark");
    expect(storedTheme()).toBeNull();
  });

  it("saves a choice and applies it", () => {
    fakeSystem(false);
    chooseTheme("dark");
    expect(theme()).toBe("dark");
    expect(window.localStorage.getItem(THEME_KEY)).toBe("dark");
  });

  it("still works when storage is blocked", () => {
    fakeSystem(true);
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    runThemeScript();
    expect(theme()).toBe("dark");
    chooseTheme("light");
    expect(theme()).toBe("light");
  });

  it("follows later system changes only while nothing is saved", () => {
    const system = fakeSystem(false);
    const unsubscribe = subscribeToTheme(() => {});

    system.change(true);
    expect(theme()).toBe("dark");

    chooseTheme("light");
    system.change(false);
    system.change(true);
    expect(theme()).toBe("light");
    unsubscribe();
  });
});
