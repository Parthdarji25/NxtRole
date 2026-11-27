"use client";

import { Tabs as TabsPrimitive } from "radix-ui";
import type { ComponentProps } from "react";

import { cn } from "@/lib/cn";

/** Underline tabs, never pills (Foundations board). Arrow keys move between tabs. */
export const Tabs = TabsPrimitive.Root;

export function TabsList({ className, ...props }: ComponentProps<typeof TabsPrimitive.List>) {
  return (
    <TabsPrimitive.List
      // Scrolls sideways on narrow phones instead of wrapping or overflowing the page.
      className={cn("flex gap-[22px] overflow-x-auto border-b border-rule", className)}
      {...props}
    />
  );
}

export function TabsTrigger({ className, ...props }: ComponentProps<typeof TabsPrimitive.Trigger>) {
  return (
    <TabsPrimitive.Trigger
      className={cn(
        "-mb-px min-h-11 shrink-0 border-b-2 border-transparent text-sm font-semibold text-ink-3",
        "data-[state=active]:border-ink data-[state=active]:text-ink",
        // Inside a scrolling list an outer ring would be cut off, so it is drawn inwards.
        "focus-visible:-outline-offset-2",
        className,
      )}
      {...props}
    />
  );
}

export function TabsContent({ className, ...props }: ComponentProps<typeof TabsPrimitive.Content>) {
  return <TabsPrimitive.Content className={cn("pt-4", className)} {...props} />;
}
