"use client";

import { Dialog as DialogPrimitive } from "radix-ui";
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { Icon } from "@/components/ui/icons";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { QUIET_EMPTY } from "@/content/emptyStates";

type Shell = { openSearch: () => void; openAgentLog: () => void };

const ShellContext = createContext<Shell | null>(null);

export function useShell(): Shell {
  const shell = useContext(ShellContext);
  if (!shell) throw new Error("useShell must be used inside <ShellProvider>");
  return shell;
}

/** Owns the two overlays every screen can open: search and the agent log. */
export function ShellProvider({ children }: { children: ReactNode }) {
  const [searchOpen, setSearchOpen] = useState(false);
  const [logOpen, setLogOpen] = useState(false);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      // Ctrl K (Cmd K on a Mac) opens search from anywhere.
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setSearchOpen(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const shell = useMemo<Shell>(
    () => ({ openSearch: () => setSearchOpen(true), openAgentLog: () => setLogOpen(true) }),
    [],
  );

  return (
    <ShellContext.Provider value={shell}>
      {children}
      <SearchDialog open={searchOpen} onOpenChange={setSearchOpen} />
      <Sheet open={logOpen} onOpenChange={setLogOpen}>
        <SheetContent
          title="Agent log"
          description="What ran while you were away. Everything can be undone."
          className="w-[min(440px,100vw)]"
        >
          <p className="border-t border-rule pt-5 text-sm text-ink-3">{QUIET_EMPTY.agentLog}</p>
        </SheetContent>
      </Sheet>
    </ShellContext.Provider>
  );
}

function SearchDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [query, setQuery] = useState("");
  const change = (next: boolean) => {
    if (!next) setQuery("");
    onOpenChange(next);
  };

  return (
    <DialogPrimitive.Root open={open} onOpenChange={change}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-40 animate-fade-in bg-scrim" />
        <DialogPrimitive.Content
          aria-describedby={undefined}
          className="fixed top-[10vh] left-1/2 z-41 flex w-[min(640px,calc(100vw-32px))] -translate-x-1/2 animate-fade-in flex-col overflow-hidden rounded-[var(--radius-panel)] border border-rule bg-paper text-ink shadow-overlay"
        >
          <DialogPrimitive.Title className="sr-only">Search</DialogPrimitive.Title>
          <div className="flex items-center gap-3 border-b border-rule px-4">
            <Icon name="search" className="text-ink-3" />
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              aria-label="Search jobs, companies, notes, questions"
              placeholder="Search jobs, companies, notes, questions…"
              maxLength={200}
              className="h-14 min-w-0 flex-1 bg-transparent text-base outline-none placeholder:text-ink-3 focus-visible:outline-none"
              autoFocus
            />
            <DialogPrimitive.Close
              aria-label="Close search"
              className="hit-target inline-flex size-8 items-center justify-center rounded-md text-ink-3"
            >
              <Icon name="close" size={16} />
            </DialogPrimitive.Close>
          </div>
          <p role="status" className="px-4 py-6 text-sm text-ink-3">
            {query.trim() ? QUIET_EMPTY.search : "Type to search."}
          </p>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
