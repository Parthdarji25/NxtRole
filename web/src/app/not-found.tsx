import type { Metadata } from "next";

import { Logo } from "@/components/layout/logo";
import { EmptyScreenState } from "@/components/states/EmptyScreenState";
import { PageHeader } from "@/components/ui/layout";

export const metadata: Metadata = { title: "Page not found" };

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-[720px] flex-col gap-7 px-5 py-8 md:px-10">
      <Logo className="self-start" />
      <PageHeader kicker="Error 404" title="This page is not here." />
      <EmptyScreenState
        content={{
          route: "404",
          title: "Check the address",
          body: "The page may have moved, or the link is wrong.",
          primary: { label: "Go to Today", href: "/today" },
        }}
      />
    </main>
  );
}
