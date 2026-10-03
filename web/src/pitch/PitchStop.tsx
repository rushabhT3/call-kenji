import type { CSSProperties, ReactNode } from "react";
import { StopHeading } from "./StopHeading.tsx";
import type { StopData } from "./stops.ts";

interface PitchStopProps {
  stop: StopData;
  number: number;
  /** Only the stop on screen takes focus and clicks; the rest of the universe is scenery. */
  isActive: boolean;
  /** On the overview every stop is a door: clicking it flies the camera there. */
  onFly: (() => void) | null;
  children: ReactNode;
}

function placementStyle({ placement }: StopData): CSSProperties {
  return {
    "--stop-x": placement.x,
    "--stop-y": placement.y,
    "--stop-scale": placement.scale,
    "--stop-rotate": placement.rotate,
  } as CSSProperties;
}

export function PitchStop({ stop, number, isActive, onFly, children }: PitchStopProps) {
  return (
    <div
      className={`pitch-stop pitch-stop--${stop.id}`}
      data-stop={stop.id}
      style={placementStyle(stop)}
    >
      <section
        className="pitch-stop__panel comic-panel"
        aria-labelledby={`stop-${stop.id}-title`}
        inert={!isActive}
      >
        <StopHeading stop={stop} number={number} />
        {children}
      </section>
      {onFly ? (
        <button type="button" className="pitch-stop__door" onClick={onFly}>
          <span className="visually-hidden">
            Fly to stop {number}: {stop.title}
          </span>
        </button>
      ) : null}
    </div>
  );
}
