"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";
import { FormProblem } from "@/components/ui/form-problem";
import { TagList } from "@/components/ui/tag-input";
import { useAction } from "@/lib/useAction";

import type { Detected, Identity } from "./types";

const schema = z.object({
  name: z
    .string()
    .trim()
    .min(2, "Enter your name as it is written in the resume.")
    .max(80, "Use 80 characters or fewer."),
});

const LISTS = [
  { key: "emails", label: "Email addresses", add: "Add an email" },
  { key: "phones", label: "Phone numbers", add: "Add a number" },
  { key: "links", label: "Links", add: "Add a link" },
  { key: "addresses", label: "Address", add: "Add an address line" },
  { key: "other", label: "Anything else", add: "Add words to hide" },
] as const;

/**
 * Before a resume is read, the owner sees what will be hidden from AI and can add to it
 * (D-053). Nothing is sent until they press the button.
 */
export function IdentityCheck({
  detected,
  saved = null,
  onConfirm,
}: {
  /** What code found in the file. */
  detected: Detected;
  /** What was confirmed for this file before, if it has been read already. */
  saved?: Identity | null;
  onConfirm: (identity: Identity) => Promise<void>;
}) {
  const [lists, setLists] = useState(() => {
    const start = saved ?? { ...detected, other: [] };
    return {
      emails: start.emails,
      phones: start.phones,
      links: start.links,
      addresses: start.addresses,
      other: start.other,
    };
  });
  const action = useAction(onConfirm);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: { name: saved?.name ?? detected.name ?? "" },
  });

  return (
    <form
      onSubmit={handleSubmit(({ name }) => action.run({ name, ...lists }))}
      noValidate
      aria-labelledby="identity-title"
      className="flex flex-col gap-4"
    >
      <div className="flex flex-col gap-1.5">
        <h2 id="identity-title" className="heading text-[26px]">
          Check what will be hidden
        </h2>
        <p className="max-w-[600px] text-ink-2">
          These are removed before your resume goes to Groq, the AI service (servers in the United
          States). Email addresses, phone numbers and ID numbers are always removed.
        </p>
      </div>

      <Field label="Your name" error={errors.name?.message} className="max-w-[420px]">
        {(control) => <Input {...control} {...register("name")} autoComplete="off" />}
      </Field>

      <div className="flex flex-col">
        {LISTS.map((list) => (
          <fieldset
            key={list.key}
            className="flex flex-col gap-2 border-t border-rule py-3.5 last:border-b"
          >
            <legend className="float-left w-full text-[15px] font-semibold">{list.label}</legend>
            <TagList
              items={lists[list.key]}
              onChange={(items) => setLists((now) => ({ ...now, [list.key]: items }))}
              addLabel={list.add}
              className="clear-left"
            />
          </fieldset>
        ))}
      </div>

      <FormProblem>{action.problem}</FormProblem>
      <div className="flex flex-wrap items-center gap-3">
        <Button type="submit" variant="primary" size="lg" loading={action.busy}>
          Hide these and read my resume
        </Button>
        <span className="text-[13px] text-ink-3">Nothing is sent until you press this.</span>
      </div>
    </form>
  );
}
