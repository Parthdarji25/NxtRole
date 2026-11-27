"use client";

import { useState } from "react";

import { ListSkeleton, PendingTag } from "@/components/states/states";
import { Badge, CountBadge, TrustBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { Dialog, DialogClose, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { Icon, type IconName } from "@/components/ui/icons";
import { PageHeader, Panel, ProgressBar, SectionHeading, StatTile } from "@/components/ui/layout";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  Tooltip,
} from "@/components/ui/menu";
import { Segmented } from "@/components/ui/segmented";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { showToast, showUndoToast } from "@/components/ui/toast";

import { ShowroomHeader } from "./ShowroomHeader";

const ICONS: IconName[] = [
  "today",
  "ask",
  "jobs",
  "pipeline",
  "followUps",
  "prepare",
  "studio",
  "resume",
  "network",
  "progress",
  "settings",
  "more",
  "offer",
  "sources",
  "logo",
  "close",
];

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="flex flex-col gap-4 border-b border-rule py-6">
      <SectionHeading title={title} />
      {children}
    </section>
  );
}

// Every label here is a generic word such as "Job title", never a made-up person or company.
export function Showroom() {
  const [on, setOn] = useState(true);
  const [chip, setChip] = useState(true);
  const [basis, setBasis] = useState<"full" | "capped">("full");

  return (
    <main className="mx-auto flex max-w-[1180px] flex-col gap-2 px-5 py-8 md:px-10">
      <ShowroomHeader
        title="Components"
        lead="Every building block in its states. Switch the theme to check dark mode."
      />

      <Block title="Buttons">
        <div className="flex flex-wrap items-center gap-3.5">
          <Button variant="primary">Apply →</Button>
          <Button>Save</Button>
          <Button variant="ink" size="sm">
            Copy and mark sent
          </Button>
          <Button variant="text">Not today</Button>
          <Button variant="primary" loading>
            Saving
          </Button>
          <Button disabled>Disabled</Button>
          <Button variant="primary" size="lg">
            Sign in
          </Button>
        </div>
      </Block>

      <Block title="Forms">
        <div className="grid max-w-3xl gap-5 md:grid-cols-2">
          <Field label="Email" hint="Used to sign in.">
            {(control) => <Input {...control} type="email" placeholder="you@example.com" />}
          </Field>
          <Field label="Email" error="Enter a valid email address.">
            {(control) => <Input {...control} type="email" defaultValue="name@" />}
          </Field>
          <Field label="Sort">
            {(control) => (
              <Select {...control} defaultValue="best">
                <option value="best">Best match</option>
                <option value="newest">Newest</option>
              </Select>
            )}
          </Field>
          <Field label="Notes">{(control) => <Textarea {...control} />}</Field>
        </div>
        <div className="flex flex-wrap items-center gap-6">
          <label className="flex items-center gap-3 text-sm">
            <Switch checked={on} onCheckedChange={setOn} aria-label="Quiet hours" />
            Quiet hours
          </label>
          <Switch checked={false} aria-label="Off example" />
          <Switch checked disabled aria-label="Disabled example" />
          <Chip pressed={chip} onPressedChange={setChip}>
            Job title
          </Chip>
          <Chip pressed={false} onPressedChange={() => {}}>
            City
          </Chip>
          <Segmented
            label="PF basis"
            value={basis}
            onChange={setBasis}
            options={[
              { value: "full", label: "Full basic" },
              { value: "capped", label: "₹15,000 cap" },
            ]}
          />
        </div>
      </Block>

      <Block title="Tabs">
        <Tabs defaultValue="fit">
          <TabsList aria-label="Job details">
            <TabsTrigger value="fit">Why it fits</TabsTrigger>
            <TabsTrigger value="people">People</TabsTrigger>
            <TabsTrigger value="company">Company</TabsTrigger>
            <TabsTrigger value="description">Description</TabsTrigger>
          </TabsList>
          <TabsContent value="fit">Reasons with quotes appear here.</TabsContent>
          <TabsContent value="people">People you know appear here.</TabsContent>
          <TabsContent value="company">Company signals appear here.</TabsContent>
          <TabsContent value="description">The job text appears here.</TabsContent>
        </Tabs>
      </Block>

      <Block title="Badges">
        <div className="flex flex-wrap items-center gap-3">
          <TrustBadge level="high" />
          <TrustBadge level="check" />
          <TrustBadge level="risky" />
          <Badge tone="blue">Reapplied</Badge>
          <Badge>Closed</Badge>
          <PendingTag />
          <CountBadge count={2} urgent />
          <CountBadge count={12} />
        </div>
      </Block>

      <Block title="Page header">
        <PageHeader
          kicker="Section label · detail"
          title="A long screen title that has to wrap onto a second line"
          lead="One sentence that says what this screen is for."
          actions={<Button>Secondary action</Button>}
        />
      </Block>

      <Block title="List row">
        <div className="flex flex-wrap items-center gap-x-5 gap-y-3 border-y border-rule py-5">
          <span className="heading w-8 text-[32px] text-ink-3">1</span>
          <div className="flex min-w-0 flex-[1_1_260px] flex-col gap-1">
            <span className="heading text-2xl">Job title</span>
            <span className="text-sm text-ink-2">Company name · City · Salary range</span>
            <span className="flex flex-wrap items-center gap-2 text-[13px] text-ink-3">
              <TrustBadge level="high" />
              <strong className="text-red">Closing date reason</strong> · What is ready
            </span>
          </div>
          <span className="font-mono text-[13px]">Score</span>
          <Button variant="primary">Apply →</Button>
        </div>
      </Block>

      <Block title="Cards and numbers">
        <div className="grid gap-5 md:grid-cols-3">
          <Panel raised className="flex flex-col gap-3">
            <span className="kicker">Tomorrow · time</span>
            <span className="heading text-[28px]">Interview round</span>
            <ProgressBar value={2} max={5} label="Prep done" />
            <span className="text-[13px] text-ink-3">Prep done 2 of 5</span>
          </Panel>
          <Panel className="grid grid-cols-2 gap-4">
            <StatTile value="–" label="waiting for a reply" />
            <StatTile value="–" label="nudges due today" />
          </Panel>
          <Panel>
            <ListSkeleton rows={1} />
          </Panel>
        </div>
      </Block>

      <Block title="Overlays and messages">
        <div className="flex flex-wrap items-center gap-3">
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="ink">Open drawer</Button>
            </SheetTrigger>
            <SheetContent title="Add a job" kicker="New">
              <Field label="Job link">
                {(control) => <Input {...control} placeholder="https://" />}
              </Field>
              <Button variant="primary">Save job</Button>
            </SheetContent>
          </Sheet>
          <Dialog>
            <DialogTrigger asChild>
              <Button>Open dialog</Button>
            </DialogTrigger>
            <DialogContent
              title="Delete all contacts?"
              description="This removes every imported contact. It cannot be undone."
            >
              <div className="flex justify-end gap-3">
                <DialogClose asChild>
                  <Button>Cancel</Button>
                </DialogClose>
                <DialogClose asChild>
                  <Button variant="ink">Delete</Button>
                </DialogClose>
              </div>
            </DialogContent>
          </Dialog>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button>Open menu</Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem>Save</DropdownMenuItem>
              <DropdownMenuItem>Not for me</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <Tooltip text="Checked word for word against the job post">
            <Button>Hover or focus me</Button>
          </Tooltip>
          <Button onClick={() => showToast("Saved.")}>Show message</Button>
          <Button onClick={() => showUndoToast("Hidden for today.", () => showToast("Restored."))}>
            Show Undo message
          </Button>
        </div>
      </Block>

      <Block title="Icons">
        <ul className="flex flex-wrap gap-5">
          {ICONS.map((name) => (
            <li key={name} className="flex w-20 flex-col items-center gap-1.5 text-xs text-ink-3">
              <Icon name={name} size={22} className="text-ink" />
              {name}
            </li>
          ))}
        </ul>
      </Block>
    </main>
  );
}
