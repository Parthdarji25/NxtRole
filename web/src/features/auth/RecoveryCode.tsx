"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";

/** A new recovery code, shown this once, with a button to copy it. */
export function RecoveryCode({ code }: { code: string }) {
  const [copied, setCopied] = useState<boolean | null>(null);

  async function copy() {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
    } catch {
      // Some browsers refuse; the code can still be selected by hand.
      setCopied(false);
    }
  }

  return (
    <div className="flex flex-col gap-3 rounded-[var(--radius-panel)] border border-rule bg-card p-[22px]">
      <span className="kicker">Your new recovery code · shown only once</span>
      <code className="font-mono text-lg leading-relaxed break-words select-all">{code}</code>
      <p className="text-sm text-ink-2">
        Write it down or keep it in a password manager. The old code no longer works.
      </p>
      <div className="flex flex-wrap items-center gap-3">
        <Button onClick={copy}>Copy code</Button>
        <span role="status" className="text-sm text-ink-2">
          {copied === true && "Copied."}
          {copied === false && "Could not copy. Select the code and copy it yourself."}
        </span>
      </div>
    </div>
  );
}
