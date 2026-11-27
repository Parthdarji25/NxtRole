import Link from "next/link";

import { SETTINGS_SECTIONS, settingsHref, type SettingsKey } from "@/content/settings";
import { cn } from "@/lib/cn";

/**
 * The Settings menu: a list down the left on desktop, and full-width rows on phones.
 * `current` is null when no section is chosen (the phone's list view).
 */
export function SettingsMenu({
  current,
  className,
}: {
  current: SettingsKey | null;
  className?: string;
}) {
  return (
    <nav aria-label="Settings sections" className={cn("flex flex-col", className)}>
      {SETTINGS_SECTIONS.map((section) => {
        const selected = section.key === current;
        return (
          <Link
            key={section.key}
            href={settingsHref(section)}
            aria-current={selected ? "page" : undefined}
            className={cn(
              "flex min-h-14 items-center justify-between gap-3 border-b border-rule text-base font-semibold no-underline",
              "md:min-h-11 md:rounded-lg md:border-b-0 md:px-3 md:text-sm",
              selected
                ? "text-ink hover:text-ink md:bg-card md:shadow-[inset_2px_0_0_var(--blue)]"
                : "text-ink md:font-medium md:text-ink-2 md:hover:bg-card",
            )}
          >
            <span className="flex min-w-0 flex-col max-md:py-2.5">
              {section.label}
              {/* The phone mock describes each section in its row. */}
              <span className="text-[13px] font-normal text-ink-3 md:hidden">{section.about}</span>
            </span>
            <span aria-hidden="true" className="text-xl text-ink-3 md:hidden">
              ›
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
