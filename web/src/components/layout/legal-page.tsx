import Link from "next/link";

import { Logo } from "@/components/layout/logo";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { PageHeader } from "@/components/ui/layout";
import type { LegalContent } from "@/content/legal";

const NAV_LINK = "inline-flex min-h-11 items-center";

/** About, Terms and Privacy share one plain page in the mock style (D-018). */
export function LegalPage({ content }: { content: LegalContent }) {
  return (
    <div className="mx-auto flex min-h-dvh max-w-[760px] flex-col gap-8 px-5 py-6 md:px-10">
      <div className="flex items-center justify-between gap-3">
        <Logo />
        <ThemeToggle />
      </div>
      <main className="flex flex-col gap-8">
        <PageHeader kicker={content.kicker} title={content.title} lead={content.lead} />
        {content.sections.map((section) => (
          <section key={section.heading} className="flex flex-col gap-3">
            <h2 className="heading text-2xl">{section.heading}</h2>
            {section.paragraphs?.map((paragraph) => (
              <p key={paragraph} className="text-ink-2">
                {paragraph}
              </p>
            ))}
            {section.points && (
              <ul className="flex list-disc flex-col gap-2 pl-5 text-ink-2">
                {section.points.map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            )}
          </section>
        ))}
      </main>
      <nav
        aria-label="Legal"
        className="mt-auto flex flex-wrap gap-5 border-t border-rule pt-4 text-sm"
      >
        <Link href="/" className={NAV_LINK}>
          Home
        </Link>
        <Link href="/about" className={NAV_LINK}>
          About
        </Link>
        <Link href="/terms" className={NAV_LINK}>
          Terms
        </Link>
        <Link href="/privacy" className={NAV_LINK}>
          Privacy
        </Link>
      </nav>
    </div>
  );
}
