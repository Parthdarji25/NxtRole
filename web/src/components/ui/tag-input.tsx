"use client";

import { useId, useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/cn";

/** The dashed "Add a title" box and its Add button, as in the Settings mock. */
export function AddItem({
  label,
  onAdd,
  inputMode,
}: {
  /** Also shown as the placeholder, for example "Add a title". */
  label: string;
  onAdd: (value: string) => void;
  inputMode?: "text" | "url";
}) {
  const id = useId();
  const [draft, setDraft] = useState("");

  function add() {
    const value = draft.trim().replace(/\s+/g, " ");
    if (value.length < 2) return;
    onAdd(value);
    setDraft("");
  }

  return (
    <span className="flex items-center gap-2">
      <label htmlFor={id} className="sr-only">
        {label}
      </label>
      <input
        id={id}
        type="text"
        inputMode={inputMode}
        maxLength={80}
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        onKeyDown={(event) => {
          if (event.key !== "Enter") return;
          event.preventDefault();
          add();
        }}
        placeholder={label}
        className="h-11 w-44 rounded-md border border-dashed border-rule-2 bg-transparent px-2.5 text-sm text-ink placeholder:text-ink-3"
      />
      <Button variant="ink" size="sm" onClick={add}>
        Add
      </Button>
    </span>
  );
}

/** Words that can be taken away one at a time, with a box to add more. */
export function TagList({
  items,
  onChange,
  addLabel,
  className,
}: {
  items: string[];
  onChange: (items: string[]) => void;
  addLabel: string;
  className?: string;
}) {
  const has = (value: string) => items.some((item) => item.toLowerCase() === value.toLowerCase());
  return (
    <div className={cn("flex flex-wrap items-center gap-2", className)}>
      {items.map((item) => (
        <span
          key={item}
          className="inline-flex min-h-9 items-center gap-1 rounded-md border border-rule-2 py-1 pr-1 pl-3 text-sm break-all"
        >
          {item}
          <button
            type="button"
            aria-label={`Remove ${item}`}
            onClick={() => onChange(items.filter((other) => other !== item))}
            className="hit-target size-7 shrink-0 text-ink-3 hover:text-ink"
          >
            <span aria-hidden="true">✕</span>
          </button>
        </span>
      ))}
      <AddItem
        label={addLabel}
        onAdd={(value) => {
          if (!has(value)) onChange([...items, value]);
        }}
      />
    </div>
  );
}
