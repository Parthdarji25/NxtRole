import type { ReactNode } from "react";

import { ShellProvider } from "./shell-context";
import { SideNav } from "./side-nav";
import { TabBar } from "./tab-bar";
import { TopBar } from "./top-bar";

/** The frame around every signed-in screen. */
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <ShellProvider>
      <a
        href="#content"
        className="sr-only z-50 rounded-lg bg-ink px-4 py-3 text-sm font-semibold text-paper focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:inline-flex focus:min-h-11 focus:items-center"
      >
        Skip to content
      </a>
      <div className="flex min-h-dvh items-stretch">
        <SideNav />
        <div className="flex min-w-0 flex-1 flex-col">
          <TopBar />
          <main
            id="content"
            tabIndex={-1}
            // Bottom space on phones keeps content above the tab bar.
            className="flex-1 px-5 pt-[22px] pb-[112px] outline-none md:px-10 md:pt-8 md:pb-16"
          >
            <div className="mx-auto flex max-w-[1180px] flex-col gap-7 md:gap-9">{children}</div>
          </main>
        </div>
        <TabBar />
      </div>
    </ShellProvider>
  );
}
