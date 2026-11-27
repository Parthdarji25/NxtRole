"use client";

import Link from "next/link";

import { Segmented } from "@/components/ui/segmented";
import { useTheme } from "@/lib/useTheme";

/** Top of the development-only showroom pages, with a theme switch. */
export function ShowroomHeader({ title, lead }: { title: string; lead: string }) {
  const [theme, setTheme] = useTheme();
  return (
    <header className="flex flex-wrap items-end justify-between gap-4 border-b-2 border-ink pb-5">
      <div className="flex flex-col gap-2">
        <span className="kicker">Development only · not in the live app</span>
        <h1 className="heading text-[40px]">{title}</h1>
        <p className="max-w-[640px] text-ink-2">{lead}</p>
        <nav aria-label="Showroom" className="flex gap-4 text-sm">
          <Link href="/design" className="inline-flex min-h-11 items-center">
            Components
          </Link>
          <Link href="/design/states" className="inline-flex min-h-11 items-center">
            Screen states
          </Link>
        </nav>
      </div>
      <Segmented
        label="Theme"
        value={theme}
        onChange={setTheme}
        options={[
          { value: "light", label: "Light" },
          { value: "dark", label: "Dark" },
        ]}
        className="w-44"
      />
    </header>
  );
}
