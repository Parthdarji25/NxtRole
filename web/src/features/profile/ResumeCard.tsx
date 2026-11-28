import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { ProgressBar } from "@/components/ui/layout";

import { PDF } from "./resumeFile";
import type { ResumeFile } from "./types";

/** The chosen file: its kind, name, what is happening to it, and how far it is. */
export function ResumeCard({
  file,
  status,
  progress,
  onReplace,
  children,
}: {
  file: Pick<ResumeFile, "name" | "content_type">;
  status: string;
  /** 0 to 100. */
  progress: number;
  onReplace?: () => void;
  children?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-4 rounded-[14px] border border-rule bg-card p-4 md:p-[22px]">
      <div className="flex items-center justify-between gap-3">
        <span className="flex min-w-0 items-center gap-3">
          <span className="rounded-md bg-ink px-2 py-2.5 font-mono text-xs text-paper">
            {file.content_type === PDF ? "PDF" : "DOCX"}
          </span>
          <span className="flex min-w-0 flex-col">
            <strong className="truncate">{file.name}</strong>
            <span role="status" className="text-[13px] text-ink-3">
              {status}
            </span>
          </span>
        </span>
        {onReplace && (
          <Button variant="text" size="sm" className="underline" onClick={onReplace}>
            Replace
          </Button>
        )}
      </div>
      <ProgressBar value={progress} max={100} label="Resume progress" className="[&>div]:bg-blue" />
      {children}
    </div>
  );
}
