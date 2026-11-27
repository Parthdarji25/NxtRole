import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { longDate } from "@/lib/dates";

import { activeNavKey, activeTabKey, MORE_LINKS, SIDE_NAV, TABS } from "./nav";
import { ShellProvider } from "./shell-context";
import { SideNav } from "./side-nav";
import { TabBar } from "./tab-bar";
import { TopBar } from "./top-bar";

const route = { pathname: "/today" };
vi.mock("next/navigation", () => ({ usePathname: () => route.pathname }));

beforeEach(() => {
  route.pathname = "/today";
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => ({ matches: false, addEventListener() {}, removeEventListener() {} })),
  );
});

describe("menus", () => {
  it("has the mock's ten side items and five phone tabs", () => {
    expect(SIDE_NAV.map((item) => item.label)).toEqual([
      "Today",
      "Ask NxtRole",
      "Jobs",
      "Pipeline",
      "Follow-ups",
      "Prepare",
      "Studio",
      "Resume",
      "Network",
      "Progress",
    ]);
    expect(TABS.map((tab) => tab.label)).toEqual(["Today", "Jobs", "Pipeline", "Prepare", "More"]);
  });

  it.each([
    ["/today/fresh", "today", "today"],
    ["/jobs/abc", "jobs", "jobs"],
    ["/pipeline/offers/1", "pipeline", "pipeline"],
    ["/follow-ups", "followUps", "pipeline"],
    ["/companies/7", "prepare", "prepare"],
    ["/prepare/3", "prepare", "prepare"],
    ["/studio/packs/2", "studio", "more"],
    ["/progress/coach", "progress", "more"],
    ["/settings/sources", "settings", "more"],
    ["/more", null, "more"],
  ])("%s highlights the right menu items", (pathname, side, tab) => {
    expect(activeNavKey(pathname)).toBe(side);
    expect(activeTabKey(pathname)).toBe(tab);
  });

  it("does not treat a look-alike address as the same section", () => {
    expect(activeNavKey("/jobs-archive")).toBeNull();
  });

  it("reaches every screen without a tab from the phone More page", () => {
    const hrefs = new Set([...MORE_LINKS.map((l) => l.href), ...TABS.map((t) => t.href)]);
    for (const item of SIDE_NAV) expect(hrefs).toContain(item.href);
    expect(hrefs).toContain("/settings");
    expect(hrefs).toContain("/progress/coach");
  });

  it("marks the current page in the side menu", () => {
    route.pathname = "/pipeline";
    render(<SideNav />);
    const menu = screen.getByRole("navigation", { name: "Main" });
    const current = within(menu).getByRole("link", { name: "Pipeline" });
    expect(current).toHaveAttribute("aria-current", "page");
    expect(within(menu).getByRole("link", { name: "Jobs" })).not.toHaveAttribute("aria-current");
  });

  it("marks the current phone tab and shows counts only when there are some", () => {
    route.pathname = "/jobs";
    render(<TabBar counts={{ today: { count: 2, urgent: true }, jobs: { count: 0 } }} />);
    expect(screen.getByRole("link", { name: /Jobs/ })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: /Today/ })).toHaveTextContent("2");
    expect(screen.getByRole("link", { name: /Jobs/ })).toHaveTextContent(/^Jobs$/);
  });
});

describe("search and agent log", () => {
  const renderBar = () =>
    render(
      <ShellProvider>
        <TopBar />
      </ShellProvider>,
    );

  it("opens search with Ctrl K, with the cursor in the box", async () => {
    renderBar();
    await userEvent.keyboard("{Control>}k{/Control}");
    const box = screen.getByRole("searchbox");
    expect(box).toHaveFocus();
    await userEvent.type(box, "react");
    expect(screen.getByRole("status")).toHaveTextContent("Nothing found.");
  });

  it("forgets the search text after closing", async () => {
    renderBar();
    await userEvent.keyboard("{Control>}k{/Control}");
    await userEvent.type(screen.getByRole("searchbox"), "react");
    await userEvent.keyboard("{Escape}");
    await userEvent.keyboard("{Control>}k{/Control}");
    expect(screen.getByRole("searchbox")).toHaveValue("");
  });

  it("opens the agent log, which says nothing has run", async () => {
    renderBar();
    await userEvent.click(screen.getByRole("button", { name: "Agent log" }));
    const dialog = screen.getByRole("dialog", { name: "Agent log" });
    expect(dialog).toHaveTextContent("Nothing has run yet.");
  });
});

describe("dates", () => {
  it("writes the date as the brief does", () => {
    expect(longDate(new Date("2026-11-27T06:00:00Z"))).toBe("Friday, 27 November");
  });

  it("uses India time, even late in the day in UTC", () => {
    // 20:00 UTC on the 27th is already 01:30 on the 28th in India.
    expect(longDate(new Date("2026-11-27T20:00:00Z"))).toBe("Saturday, 28 November");
  });
});
