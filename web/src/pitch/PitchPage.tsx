import "../showcase/showcase.css";
import "../showcase/diagrams.css";
import "./pitch.css";
import { useMemo, useRef } from "react";
import { PitchControls } from "./PitchControls.tsx";
import { PitchWorld } from "./PitchWorld.tsx";
import { LAST_STEP, OVERVIEW_STEP, stepLabel } from "./stops.ts";
import { usePitch } from "./usePitch.ts";
import { usePitchSwipe } from "./usePitchSwipe.ts";

function announcement(step: number): string {
  return step === OVERVIEW_STEP
    ? "Map of the whole universe"
    : `Stop ${String(step)} of ${String(LAST_STEP)}: ${stepLabel(step)}`;
}

/** Kenji's Universe: the whole story on one comic canvas that the camera flies across. */
export function PitchPage() {
  const viewport = useRef<HTMLDivElement>(null);
  const camera = useRef<HTMLDivElement>(null);
  const world = useRef<HTMLDivElement>(null);
  const refs = useMemo(() => ({ viewport, camera, world }), [viewport, camera, world]);
  const pitch = usePitch(refs);
  const { isCanvas, position, moves } = pitch;
  const swipe = usePitchSwipe(moves.next, moves.previous);
  return (
    <div className={isCanvas ? "showcase pitch pitch--canvas" : "showcase pitch"}>
      <title>Kenji's Universe · Call Kenji</title>
      <div ref={viewport} className="pitch__viewport" {...(isCanvas ? swipe : {})}>
        <div ref={camera} className="pitch__camera">
          <PitchWorld ref={world} step={position.step} isCanvas={isCanvas} onJump={moves.jump} />
        </div>
      </div>
      {isCanvas ? (
        <PitchControls
          position={position}
          pageCounts={pitch.pageCounts}
          isPlaying={pitch.isPlaying}
          moves={moves}
          onTogglePlay={pitch.togglePlay}
        />
      ) : null}
      <p className="visually-hidden" aria-live="polite">
        {isCanvas ? announcement(position.step) : ""}
      </p>
    </div>
  );
}
