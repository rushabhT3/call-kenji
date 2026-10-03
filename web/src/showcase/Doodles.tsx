const LINES = [
  { tone: "orange", d: "M-20 60 C 60 20, 120 120, 210 70 S 330 10, 400 60" },
  { tone: "teal", d: "M-30 220 C 40 170, 90 290, 180 250" },
  { tone: "green", d: "M1080 40 C 1160 10, 1210 110, 1300 80 S 1420 30, 1480 90" },
  { tone: "blue", d: "M1150 300 C 1220 250, 1290 350, 1380 300 S 1460 260, 1500 300" },
  { tone: "orange", d: "M980 520 C 1060 470, 1130 580, 1220 540" },
  { tone: "teal", d: "M60 560 C 120 500, 200 620, 300 560" },
] as const;

/** The coloured lines scribbled behind the reference burst. Decoration only. */
export function Doodles() {
  return (
    <svg
      className="doodles"
      viewBox="0 0 1440 640"
      preserveAspectRatio="xMidYMid slice"
      aria-hidden="true"
      focusable="false"
    >
      {LINES.map((line) => (
        <path key={line.d} className={`doodle doodle--${line.tone}`} d={line.d} />
      ))}
    </svg>
  );
}
