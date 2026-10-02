export type IconName =
  "phone" | "check" | "cross" | "clock" | "copy" | "mic" | "end" | "arrowDown" | "pause" | "sound";

const PATHS: Record<IconName, string> = {
  phone:
    "M5 4h3l1.5 4-2 1.2a11 11 0 0 0 5.3 5.3L14 12.5l4 1.5v3a2 2 0 0 1-2 2A13 13 0 0 1 3 6a2 2 0 0 1 2-2z",
  check: "M4.5 12.5l5 5 10-11",
  cross: "M6 6l12 12M18 6L6 18",
  clock: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 7v5l3 2",
  copy: "M9 9h10v10H9zM5 15V5h10",
  mic: "M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3zM5 11a7 7 0 0 0 14 0M12 18v3",
  end: "M3 14c5-4 13-4 18 0l-2 3-4-1v-3a10 10 0 0 0-6 0v3l-4 1z",
  arrowDown: "M12 5v14M6 13l6 6 6-6",
  pause: "M9 5v14M15 5v14",
  sound: "M4 9h4l5-4v14l-5-4H4zM16.5 9.5a3.5 3.5 0 0 1 0 5M19 7a7 7 0 0 1 0 10",
};

/** The stroke reads as 1.5px at 20px; smaller icons get a proportionally heavier stroke. */
const STROKE_AT_DEFAULT_SIZE = 30;

interface IconProps {
  name: IconName;
  size?: number;
}

export function Icon({ name, size = 20 }: IconProps) {
  return (
    <svg
      className="icon"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={STROKE_AT_DEFAULT_SIZE / size}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <path d={PATHS[name]} />
    </svg>
  );
}
