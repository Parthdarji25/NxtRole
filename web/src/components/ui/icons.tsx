/**
 * Line icons copied from the mocks (docs/mocks/source/Nav, MTabs, TopBar, Landing).
 * They are decoration: the text next to them carries the meaning, so they are hidden from
 * screen readers.
 */
const PATHS = {
  today: "M4 5h13v14H6a2 2 0 0 1-2-2zM17 8h3v9a2 2 0 0 1-2 2M8 9h5M8 13h5M8 16h3",
  ask: "M4 5h16v11H9l-5 4zM9 10.5h.01M12 10.5h.01M15 10.5h.01",
  jobs: "M5 11a6 6 0 1 0 12 0a6 6 0 1 0-12 0M20 20l-4.3-4.3",
  pipeline: "M3 4h5v16H3zM10 4h5v11h-5zM17 4h4v7h-4z",
  followUps: "M12 8v4l2.5 2.5M4 12a8 8 0 1 0 16 0a8 8 0 1 0-16 0",
  prepare: "M4 12a8 8 0 1 0 16 0a8 8 0 1 0-16 0M8 12a4 4 0 1 0 8 0a4 4 0 1 0-8 0",
  studio: "M4 20h4L19 9l-4-4L4 16zM13 7l4 4",
  resume: "M6 3h9l4 4v14H6zM14 3v5h5M9 12h7M9 16h7",
  network:
    "M8 9a3 3 0 1 0 0-6a3 3 0 1 0 0 6M2 20a6 6 0 0 1 12 0M17 11a2.5 2.5 0 1 0 0-5a2.5 2.5 0 1 0 0 5M15.5 14.2A5 5 0 0 1 22 19",
  progress: "M4 20V10M10 20V4M16 20v-7M2 20h20",
  settings:
    "M4 7h10M18 7h2M4 17h4M12 17h8M14 7a2 2 0 1 0 4 0a2 2 0 1 0-4 0M8 17a2 2 0 1 0 4 0a2 2 0 1 0-4 0",
  more: "M4 12a1.5 1.5 0 1 0 3 0a1.5 1.5 0 1 0-3 0M10.5 12a1.5 1.5 0 1 0 3 0a1.5 1.5 0 1 0-3 0M17 12a1.5 1.5 0 1 0 3 0a1.5 1.5 0 1 0-3 0",
  offer: "M3 7h18v10H3zM7 12h.01M17 12h.01M12 14.5a2.5 2.5 0 1 0 0-5a2.5 2.5 0 1 0 0 5",
  sources:
    "M5 7a7 3 0 1 0 14 0a7 3 0 1 0-14 0M5 7v10c0 1.7 3.1 3 7 3s7-1.3 7-3V7M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3",
  search: "M5 11a6 6 0 1 0 12 0a6 6 0 1 0-12 0M20 20l-4.3-4.3",
  logo: "M7 4h10a3 3 0 0 1 3 3v10a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V7a3 3 0 0 1 3-3zM9 12h6M13 9l3 3-3 3",
  close: "M6 6l12 12M18 6L6 18",
  moon: "M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z",
  sun: "M8 12a4 4 0 1 0 8 0a4 4 0 1 0-8 0M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4",
} as const;

export type IconName = keyof typeof PATHS;

export function Icon({
  name,
  size = 18,
  className,
}: {
  name: IconName;
  size?: number;
  className?: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      className={className}
    >
      <path d={PATHS[name]} />
    </svg>
  );
}
