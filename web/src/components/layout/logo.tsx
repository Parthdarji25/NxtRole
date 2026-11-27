import Link from "next/link";

import { Icon } from "@/components/ui/icons";
import { cn } from "@/lib/cn";

/** "Nxt" in ink and "Role" in blue, everywhere (CLAUDE.md rule 6). */
export function Logo({
  className,
  compact = false,
  large = false,
}: {
  className?: string;
  compact?: boolean;
  large?: boolean;
}) {
  return (
    <Link
      href="/"
      aria-label="NxtRole home"
      className={cn(
        "hit-target inline-flex items-center gap-2 text-ink no-underline hover:text-ink",
        className,
      )}
    >
      <Icon name="logo" size={large ? 24 : 20} className="text-blue" />
      <span
        aria-hidden="true"
        className={cn(
          "text-[23px] leading-none font-bold tracking-[-0.03em]",
          large && "text-[26px] md:text-[28px]",
          // In the narrow side menu only the icon fits.
          compact && "md:hidden lg:inline",
        )}
      >
        Nxt<span className="text-blue">Role</span>
      </span>
    </Link>
  );
}
