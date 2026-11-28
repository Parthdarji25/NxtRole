"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/field";

import { KINDS, newFactId } from "./facts";
import type { Fact, FactKind } from "./types";

const short = z.string().trim().max(160, "Use 160 characters or fewer.");

const schema = z.object({
  kind: z.enum(KINDS.map((entry) => entry.kind) as [FactKind, ...FactKind[]]),
  value: z.string().trim().min(1, "Write the fact.").max(500, "Use 500 characters or fewer."),
  company: short,
  dates: short,
});

/**
 * Writes or changes one fact. What the owner writes is theirs: it no longer carries a quote
 * from the resume.
 */
export function FactForm({
  fact,
  onSave,
  onCancel,
}: {
  /** The fact being changed; none when adding. */
  fact?: Fact;
  onSave: (fact: Fact) => void;
  onCancel: () => void;
}) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: {
      kind: fact?.kind ?? "skill",
      value: fact?.value ?? "",
      company: fact?.company ?? "",
      dates: fact?.dates ?? "",
    },
  });

  const save = handleSubmit((typed) => {
    const next = {
      kind: typed.kind,
      value: typed.value,
      company: typed.company || null,
      dates: typed.dates || null,
    };
    const unchanged =
      fact &&
      fact.value === next.value &&
      fact.company === next.company &&
      fact.dates === next.dates;
    onSave(
      unchanged
        ? fact
        : { ...next, fact_id: fact?.fact_id ?? newFactId(), quote: null, source: "you" },
    );
  });

  return (
    <form
      onSubmit={save}
      noValidate
      aria-label={fact ? `Change ${fact.value}` : "Add a fact"}
      className="flex flex-col gap-3 rounded-[var(--radius-panel)] border border-rule-2 bg-card p-4"
    >
      {!fact && (
        <Field label="Kind of fact" className="items-start">
          {(control) => (
            <Select {...control} {...register("kind")}>
              {KINDS.map((entry) => (
                <option key={entry.kind} value={entry.kind}>
                  {entry.one}
                </option>
              ))}
            </Select>
          )}
        </Field>
      )}
      <Field label="Fact" error={errors.value?.message}>
        {(control) => (
          <Textarea {...control} {...register("value")} rows={2} className="min-h-16" />
        )}
      </Field>
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Company (optional)" error={errors.company?.message}>
          {(control) => <Input {...control} {...register("company")} />}
        </Field>
        <Field label="Dates (optional)" error={errors.dates?.message}>
          {(control) => <Input {...control} {...register("dates")} />}
        </Field>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button type="submit" variant="ink">
          {fact ? "Keep change" : "Add"}
        </Button>
        <Button variant="text" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
