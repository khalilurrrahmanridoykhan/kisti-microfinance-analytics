/** A small set of line icons (24px grid, 1.8 stroke, currentColor), drawn inline so the
 * dashboard needs no icon font or extra request. Decorative only: always aria-hidden. */
const PATHS: Record<string, string> = {
  institution: "M3 21h18M4 10h16M12 3l8 5H4l8-5zM6 10v8M10 10v8M14 10v8M18 10v8",
  banknote: "M3 7h18v10H3zM7 7v10M17 7v10M12 10a2 2 0 1 1 0 4a2 2 0 0 1 0-4z",
  users: "M16 20v-1.5a3.5 3.5 0 0 0-3.5-3.5h-5A3.5 3.5 0 0 0 4 18.5V20M10 11a3.5 3.5 0 1 0 0-7a3.5 3.5 0 0 0 0 7zM20 20v-1.5a3.5 3.5 0 0 0-2.5-3.35M15.5 4.15a3.5 3.5 0 0 1 0 6.7",
  member: "M4 20v-1a5 5 0 0 1 5-5h2M9 11a3.5 3.5 0 1 0 0-7a3.5 3.5 0 0 0 0 7zM17 14v6M14 17h6",
  savings: "M19 9.5V8a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-1.5M15 12.5h6v-3h-6a1.5 1.5 0 0 0 0 3z",
  pin: "M12 21s-7-6.2-7-11.5a7 7 0 1 1 14 0C19 14.8 12 21 12 21zM12 12a2.5 2.5 0 1 0 0-5a2.5 2.5 0 0 0 0 5z",
  pie: "M12 3v9h9M21 12a9 9 0 1 1-9-9",
  alert: "M12 4l9 16H3l9-16zM12 10v4M12 17v.01",
  scale: "M12 4v16M5 20h14M5 8l-3 6a3 3 0 0 0 6 0L5 8zM19 8l-3 6a3 3 0 0 0 6 0l-3-6zM5 8h14",
  map: "M9 4L3 6.5v13.5l6-2.5l6 2.5l6-2.5V4l-6 2.5L9 4zM9 4v14M15 6.5v14",
  arrow: "M5 12h14M13 6l6 6l-6 6",
};

export type IconName = keyof typeof PATHS;

export function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <path d={PATHS[name]} />
    </svg>
  );
}
