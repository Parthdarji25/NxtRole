import Link from "next/link";
import type { ReactNode } from "react";

import { PageHeader } from "@/components/ui/layout";

export type Back = { label: string; href: string };

/** "‹ More": the way back on phone screens, which have no side menu. */
export function BackLink({ label, href }: Back) {
  return (
    <Link
      href={href}
      className="-mb-4 inline-flex min-h-11 items-center gap-1 self-start font-semibold no-underline md:hidden"
    >
      <span aria-hidden="true">‹</span> {label}
    </Link>
  );
}

/** A screen: optional way back, the page header and the content below it. */
export function Screen({
  title,
  kicker,
  lead,
  phoneTitle,
  phoneLead,
  back,
  actions,
  children,
}: {
  title: string;
  kicker?: string;
  lead?: ReactNode;
  phoneTitle?: string;
  phoneLead?: string;
  back?: Back;
  actions?: ReactNode;
  children?: ReactNode;
}) {
  return (
    <>
      {back && <BackLink {...back} />}
      <PageHeader
        title={title}
        kicker={kicker}
        lead={lead}
        phoneTitle={phoneTitle}
        phoneLead={phoneLead}
        actions={actions}
      />
      {children}
    </>
  );
}
