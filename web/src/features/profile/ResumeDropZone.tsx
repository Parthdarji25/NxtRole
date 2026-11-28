"use client";

import { useId, useState } from "react";

import { FormProblem } from "@/components/ui/form-problem";
import { cn } from "@/lib/cn";

import { ACCEPT, problemWith } from "./resumeFile";

/** The dashed box of Onboarding step 1: tap to choose a file, or drop one on it. */
export function ResumeDropZone({
  onFile,
  problem = null,
}: {
  onFile: (file: File) => void;
  /** Why the last upload was refused. */
  problem?: string | null;
}) {
  const id = useId();
  const [over, setOver] = useState(false);
  const [refused, setRefused] = useState<string | null>(null);

  function take(file: File | undefined) {
    if (!file) return;
    const reason = problemWith(file);
    setRefused(reason);
    if (!reason) onFile(file);
  }

  return (
    <div className="flex flex-col gap-3">
      <label
        htmlFor={id}
        onDragOver={(event) => {
          event.preventDefault();
          setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={(event) => {
          event.preventDefault();
          setOver(false);
          take(event.dataTransfer.files[0]);
        }}
        className={cn(
          "flex cursor-pointer flex-col items-center gap-1.5 rounded-[14px] border-[1.5px]",
          "border-dashed border-rule-2 bg-card px-4 py-7 text-center md:gap-2.5 md:px-6 md:py-12",
          // The hidden input is what receives keyboard focus; the box shows it.
          "has-focus-visible:outline-2 has-focus-visible:outline-offset-2 has-focus-visible:outline-blue",
          over && "border-blue bg-blue-soft",
        )}
      >
        <svg
          width="28"
          height="28"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M12 16V4M7 9l5-5 5 5M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3" />
        </svg>
        <span className="font-semibold md:hidden">Upload your resume</span>
        <span className="heading text-2xl max-md:hidden">Choose a PDF or Word file</span>
        <span className="text-[13px] text-ink-3 md:hidden">PDF or Word, up to 5 MB</span>
        <span className="text-[13px] text-ink-3 max-md:hidden">or drop it here · up to 5 MB</span>
        <input
          id={id}
          type="file"
          accept={ACCEPT}
          className="sr-only"
          onChange={(event) => {
            take(event.target.files?.[0]);
            // Choosing the same file again must work after a refusal.
            event.target.value = "";
          }}
        />
      </label>
      <FormProblem>{refused ?? problem}</FormProblem>
    </div>
  );
}
