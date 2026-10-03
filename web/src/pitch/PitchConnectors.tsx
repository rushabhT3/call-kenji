import { doodlePath } from "./camera.ts";
import { STOPS, WORLD } from "./stops.ts";

const TONES = ["orange", "teal", "green", "blue", "red"] as const;
/** How far each doodle bows away from a straight line, alternating sides like a hand would. */
const BOW = 0.18;

const PATHS = STOPS.slice(1).map((stop, index) => {
  const from = STOPS[index]?.placement ?? stop.placement;
  return {
    id: stop.id,
    tone: TONES[index % TONES.length] ?? "orange",
    d: doodlePath(from, stop.placement, index % 2 === 0 ? BOW : -BOW),
  };
});

/** The trail of coloured doodles that joins the stops in story order. Decoration only. */
export function PitchConnectors() {
  return (
    <svg
      className="pitch-trail"
      viewBox={`0 0 ${String(WORLD.width)} ${String(WORLD.height)}`}
      aria-hidden="true"
      focusable="false"
    >
      {PATHS.map((path) => (
        <path
          key={path.id}
          className={`pitch-trail__line pitch-trail__line--${path.tone}`}
          d={path.d}
        />
      ))}
    </svg>
  );
}
