/**
 * Light and dark theme. The choice is stored on this device; without a stored choice the
 * system setting is followed (FR-205).
 */
export type Theme = "light" | "dark";

export const THEME_KEY = "nxtrole-theme";
const DARK_QUERY = "(prefers-color-scheme: dark)";

/**
 * Runs in <head> before the page is painted, so the wrong theme never flashes.
 * It is a fixed string with no outside input.
 */
export const THEME_SCRIPT = `(function(){var t=null;try{t=localStorage.getItem("${THEME_KEY}")}catch(e){}if(t!=="light"&&t!=="dark"){t=window.matchMedia("${DARK_QUERY}").matches?"dark":"light"}document.documentElement.setAttribute("data-theme",t)})()`;

export function storedTheme(): Theme | null {
  try {
    const value = window.localStorage.getItem(THEME_KEY);
    return value === "light" || value === "dark" ? value : null;
  } catch {
    // Storage can be blocked (private windows); the app still works.
    return null;
  }
}

export function systemTheme(): Theme {
  return window.matchMedia(DARK_QUERY).matches ? "dark" : "light";
}

export function currentTheme(): Theme {
  return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
}

export function applyTheme(theme: Theme): void {
  document.documentElement.setAttribute("data-theme", theme);
}

export function chooseTheme(theme: Theme): void {
  try {
    window.localStorage.setItem(THEME_KEY, theme);
  } catch {
    // Not saved, but still applied for this visit.
  }
  applyTheme(theme);
}

/** Calls `onChange` whenever the theme on the page changes, from any source. */
export function subscribeToTheme(onChange: () => void): () => void {
  const observer = new MutationObserver(onChange);
  observer.observe(document.documentElement, { attributeFilter: ["data-theme"] });

  // The system setting changed and the user has not chosen a theme themselves.
  const media = window.matchMedia(DARK_QUERY);
  const followSystem = () => {
    if (!storedTheme()) applyTheme(systemTheme());
  };
  media.addEventListener("change", followSystem);

  // The theme was changed in another tab.
  const followOtherTab = (event: StorageEvent) => {
    if (event.key === THEME_KEY) applyTheme(storedTheme() ?? systemTheme());
  };
  window.addEventListener("storage", followOtherTab);

  return () => {
    observer.disconnect();
    media.removeEventListener("change", followSystem);
    window.removeEventListener("storage", followOtherTab);
  };
}
