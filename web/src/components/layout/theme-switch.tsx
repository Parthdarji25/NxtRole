"use client";

import { Segmented } from "@/components/ui/segmented";
import { useTheme } from "@/lib/useTheme";

export function ThemeSwitch({ className }: { className?: string }) {
  const [theme, setTheme] = useTheme();
  return (
    <Segmented
      label="Theme"
      value={theme}
      onChange={setTheme}
      options={[
        { value: "light", label: "Light" },
        { value: "dark", label: "Dark" },
      ]}
      className={className}
    />
  );
}
