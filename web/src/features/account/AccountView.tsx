"use client";

import { useState, type ReactNode } from "react";

import { ErrorState, ListSkeleton } from "@/components/states/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogClose, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { Input, Label } from "@/components/ui/field";
import { FormProblem } from "@/components/ui/form-problem";
import { shortDateTime } from "@/lib/dates";
import { deviceName } from "@/lib/device";
import type { User } from "@/lib/session";
import { useAction } from "@/lib/useAction";

import { ChangePassword, type PasswordValues } from "./ChangePassword";

export const MAX_NAME = 80;

export type Device = {
  family_id: string;
  signed_in_at: string;
  last_used_at: string;
  user_agent: string | null;
  ip_hint: string | null;
  current: boolean;
};

export type DeviceList =
  | { status: "loading" }
  | { status: "error"; message: string; retry: () => void }
  | { status: "ready"; items: Device[] };

export type AccountActions = {
  saveName: (name: string | null) => Promise<unknown>;
  changePassword: (values: PasswordValues) => Promise<unknown>;
  signOutDevice: (familyId: string) => Promise<unknown>;
  signOut: () => Promise<unknown>;
  signOutEverywhere: () => Promise<unknown>;
};

/** One setting: what it is on the left, its control on the right (the Accounts mock's rows). */
function Row({ title, hint, children }: { title: string; hint: string; children?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-t border-rule py-[18px]">
      <div className="flex min-w-0 flex-[1_1_220px] flex-col">
        <span className="font-semibold">{title}</span>
        <span className="text-[13px] break-words text-ink-3">{hint}</span>
      </div>
      {children}
    </div>
  );
}

function NameRow({ name, onSave }: { name: string | null; onSave: AccountActions["saveName"] }) {
  const [value, setValue] = useState(name ?? "");
  const [shownFor, setShownFor] = useState(name);
  // Follow a change made elsewhere, such as Undo.
  if (shownFor !== name) {
    setShownFor(name);
    setValue(name ?? "");
  }
  const save = useAction(onSave);
  const trimmed = value.trim();

  return (
    <form
      noValidate
      onSubmit={(event) => {
        event.preventDefault();
        void save.run(trimmed || null);
      }}
      className="flex flex-col gap-2 border-t border-rule py-[18px]"
    >
      <Label htmlFor="display-name" className="text-[15px]">
        Your name
      </Label>
      <span id="display-name-hint" className="text-[13px] text-ink-3">
        Shown on your screens, for example in the morning greeting. Never sent to AI.
      </span>
      <div className="flex flex-wrap gap-3">
        <Input
          id="display-name"
          aria-describedby="display-name-hint"
          value={value}
          maxLength={MAX_NAME}
          autoComplete="given-name"
          onChange={(event) => setValue(event.target.value)}
          className="h-11 max-w-sm flex-[1_1_220px]"
        />
        <Button type="submit" loading={save.busy} disabled={trimmed === (name ?? "")}>
          Save name
        </Button>
      </div>
      <FormProblem>{save.problem}</FormProblem>
    </form>
  );
}

function Devices({
  devices,
  onSignOut,
}: {
  devices: DeviceList;
  onSignOut: AccountActions["signOutDevice"];
}) {
  const signOut = useAction(onSignOut);

  if (devices.status === "loading") return <ListSkeleton rows={2} label="Loading devices" />;
  if (devices.status === "error") {
    return (
      <ErrorState onRetry={devices.retry} className="border-b-0">
        {devices.message}
      </ErrorState>
    );
  }
  return (
    <>
      <FormProblem>{signOut.problem}</FormProblem>
      <ul className="flex flex-col">
        {devices.items.map((device) => {
          const name = deviceName(device.user_agent);
          return (
            <li
              key={device.family_id}
              className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-t border-rule py-3.5"
            >
              <div className="flex min-w-0 flex-[1_1_220px] flex-col gap-0.5">
                <span className="flex flex-wrap items-center gap-2 font-semibold">
                  {name}
                  {device.current && <Badge tone="blue">This device</Badge>}
                </span>
                <span className="text-[13px] text-ink-3">
                  Last used {shortDateTime(new Date(device.last_used_at))} · signed in{" "}
                  {shortDateTime(new Date(device.signed_in_at))}
                </span>
              </div>
              {!device.current && (
                <Button
                  size="sm"
                  disabled={signOut.busy}
                  onClick={() => void signOut.run(device.family_id)}
                  aria-label={`Sign out ${name}`}
                >
                  Sign out
                </Button>
              )}
            </li>
          );
        })}
      </ul>
    </>
  );
}

/** Settings > Accounts (FR-009, FR-010). */
export function AccountView({
  user,
  devices,
  actions,
}: {
  user: User;
  devices: DeviceList;
  actions: AccountActions;
}) {
  const signOut = useAction(actions.signOut);
  const everywhere = useAction(actions.signOutEverywhere);

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col">
        <NameRow name={user.display_name} onSave={actions.saveName} />
        <Row title="Email" hint={user.email}>
          <span className="text-[13px] text-ink-3">Used to sign in</span>
        </Row>
        <Row title="Password" hint="Changing it signs out your other devices.">
          <ChangePassword onChange={actions.changePassword} />
        </Row>
      </div>

      <section aria-labelledby="devices-title" className="flex flex-col gap-3">
        <h3 id="devices-title" className="heading text-xl">
          Signed-in devices
        </h3>
        <Devices devices={devices} onSignOut={actions.signOutDevice} />
        <div className="flex flex-wrap gap-3 border-t border-rule pt-4">
          <Button loading={signOut.busy} onClick={() => void signOut.run()}>
            Sign out
          </Button>
          <Dialog>
            <DialogTrigger asChild>
              <Button variant="text">Sign out everywhere</Button>
            </DialogTrigger>
            <DialogContent
              title="Sign out everywhere?"
              description="Every device, this one included, will need your password again."
            >
              <FormProblem>{everywhere.problem}</FormProblem>
              <div className="flex flex-wrap justify-end gap-3">
                <DialogClose asChild>
                  <Button>Cancel</Button>
                </DialogClose>
                <Button
                  variant="ink"
                  loading={everywhere.busy}
                  onClick={() => void everywhere.run()}
                >
                  Sign out everywhere
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
        <FormProblem>{signOut.problem}</FormProblem>
      </section>

      <section aria-labelledby="data-title" className="flex flex-col items-start gap-3">
        <h3 id="data-title" className="heading text-xl">
          Your data
        </h3>
        <div className="flex flex-wrap gap-3">
          <Button disabled aria-describedby="data-note">
            Export my data
          </Button>
          <Button disabled aria-describedby="data-note">
            Delete my account and data
          </Button>
        </div>
        <p id="data-note" className="text-[13px] text-ink-3">
          These arrive with a later update.
        </p>
      </section>
    </div>
  );
}
