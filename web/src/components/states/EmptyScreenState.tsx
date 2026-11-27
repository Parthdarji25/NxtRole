import Link from "next/link";

import { Button } from "@/components/ui/button";
import type { EmptyContent } from "@/content/emptyStates";

import { EmptyState } from "./states";

/** The empty state of a whole screen, built from the shared wording. */
export function EmptyScreenState({ content }: { content: EmptyContent }) {
  const { primary, secondary } = content;
  return (
    <EmptyState
      title={content.title}
      action={
        (primary || secondary) && (
          <>
            {primary && (
              <Button asChild variant="primary">
                <Link href={primary.href}>
                  {primary.label} <span aria-hidden="true">→</span>
                </Link>
              </Button>
            )}
            {secondary && (
              <Button asChild variant="outline">
                <Link href={secondary.href}>{secondary.label}</Link>
              </Button>
            )}
          </>
        )
      }
    >
      {content.body}
    </EmptyState>
  );
}
