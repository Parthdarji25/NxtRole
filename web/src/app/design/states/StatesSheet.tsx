"use client";

import type { ReactNode } from "react";

import { EmptyScreenState } from "@/components/states/EmptyScreenState";
import {
  Banner,
  ErrorState,
  ListSkeleton,
  OfflineNotice,
  PageSkeleton,
  PendingTag,
} from "@/components/states/states";
import { Button } from "@/components/ui/button";
import { PageHeader, SectionHeading } from "@/components/ui/layout";
import { EMPTY_STATES, QUIET_EMPTY } from "@/content/emptyStates";

import { ShowroomHeader } from "../ShowroomHeader";

function Sample({
  number,
  title,
  note,
  children,
}: {
  number: string;
  title: string;
  note: string;
  children: ReactNode;
}) {
  return (
    <section className="flex flex-col gap-4 py-8">
      <SectionHeading title={`${number}. ${title}`} aside={note} />
      <div className="rounded-[var(--radius-panel)] border border-dashed border-rule-2 p-5 md:p-8">
        {children}
      </div>
    </section>
  );
}

export function StatesSheet() {
  const screens = Object.values(EMPTY_STATES);
  return (
    <main className="mx-auto flex max-w-[1180px] flex-col px-5 py-8 md:px-10">
      <ShowroomHeader
        title="Screen states"
        lead="The loading, empty, error and waiting states the mocks do not draw. Nothing here is example data. Please approve the look and the wording before they are used on every screen."
      />

      <Sample number="1" title="Loading" note="Shown while a screen's data is on its way">
        <PageSkeleton rows={3} label="Loading your brief" />
      </Sample>

      <Sample number="2" title="Empty screen" note="First visit to Today">
        <div className="flex flex-col gap-8">
          <PageHeader
            kicker="Today · your brief"
            title="Good morning."
            lead="Your short list appears here every morning."
          />
          <EmptyScreenState content={EMPTY_STATES.today} />
        </div>
      </Sample>

      <Sample number="3" title="Empty part of a screen" note="Quiet text, as in the mocks">
        <div className="flex flex-col divide-y divide-rule">
          <p className="py-7 text-ink-3">{QUIET_EMPTY.pipelineStage}</p>
          <div className="flex flex-wrap items-center gap-3 py-7 text-sm text-ink-3">
            {QUIET_EMPTY.filteredJobs}
            <Button size="sm">Clear filters</Button>
          </div>
          <p className="py-7 text-sm text-ink-3">{QUIET_EMPTY.search}</p>
          <p className="py-7 text-sm text-ink-3">{QUIET_EMPTY.agentLog}</p>
        </div>
      </Sample>

      <Sample number="4" title="Error" note="Something failed; offer to try again">
        <ErrorState title="Your jobs did not load" onRetry={() => {}} />
      </Sample>

      <Sample number="5" title="Offline, out of date and waiting" note="Coloured bands and tags">
        <div className="flex flex-col gap-4">
          <OfflineNotice />
          <Banner tone="amber" tag="Older brief" action={<Button size="sm">Try again</Button>}>
            This morning&rsquo;s search did not finish. You are seeing the last brief.
          </Banner>
          <Banner tone="amber" tag="Source paused" action={<Button size="sm">Retry now</Button>}>
            One job source stopped answering. The others are still working.
          </Banner>
          <Banner tone="blue" tag="Using backup model">
            The main AI model used its free limit. Drafts are being written as normal.
          </Banner>
          <Banner tone="red" tag="All AI limits used">
            Job search and checks keep running. Drafts wait and are tried again every hour.
          </Banner>
          <div className="flex items-center gap-3 border-y border-rule py-4">
            <span className="flex-1">Resume and note for this job</span>
            <PendingTag />
          </div>
          <ListSkeleton rows={1} label="Loading more" />
        </div>
      </Sample>

      <Sample number="6" title="Page not found" note="An address that does not exist">
        <div className="flex flex-col gap-6">
          <PageHeader kicker="Error 404" title="This page is not here." />
          <EmptyScreenState
            content={{
              route: "404",
              title: "Check the address",
              body: "The page may have moved, or the link is wrong.",
              primary: { label: "Go to Today", href: "/today" },
            }}
          />
        </div>
      </Sample>

      <section className="flex flex-col gap-4 py-8">
        <SectionHeading
          title="7. Wording for every screen"
          aside={`${screens.length} empty states`}
        />
        <div className="grid gap-x-10 md:grid-cols-2">
          {screens.map((content) => (
            <div key={content.route} className="flex min-w-0 flex-col gap-2 pt-6">
              <code className="font-mono text-xs break-all text-ink-3">{content.route}</code>
              <EmptyScreenState content={content} />
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
