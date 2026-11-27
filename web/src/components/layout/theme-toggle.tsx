"use client";

import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icons";
import { cn } from "@/lib/cn";
import { useTheme } from "@/lib/useTheme";

/**
 * One button that switches the theme and names the theme it will switch to.
 * The Landing mocks add an icon and, on phones, show the icon alone.
 */
export function ThemeToggle({ withIcon = false }: { withIcon?: boolean }) {
  const [theme, setTheme] = useTheme();
  const next = theme === "dark" ? "light" : "dark";
  return (
    <Button
      size="sm"
      onClick={() => setTheme(next)}
      aria-label={`Switch to ${next} theme`}
      className={cn("font-normal text-ink-2", withIcon && "max-md:w-11 max-md:px-0")}
    >
      {withIcon && <Icon name={next === "dark" ? "moon" : "sun"} size={15} />}
      <span className={cn(withIcon && "max-md:hidden")}>{next === "dark" ? "Dark" : "Light"}</span>
    </Button>
  );
}
