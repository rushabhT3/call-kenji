import type { CSSProperties, Ref } from "react";
import { Burst } from "../showcase/Burst.tsx";
import { PitchConnectors } from "./PitchConnectors.tsx";
import { PitchStop } from "./PitchStop.tsx";
import { StopContent } from "./StopContent.tsx";
import {
  CENTRE_BURST,
  firstStepOf,
  OVERVIEW_STEP,
  STEPS,
  STOPS,
  WORLD,
  type StopId,
} from "./stops.ts";

interface PitchWorldProps {
  ref: Ref<HTMLDivElement>;
  step: number;
  isCanvas: boolean;
  onJump: (step: number) => void;
}

const WORLD_STYLE = {
  "--world-width": WORLD.width,
  "--world-height": WORLD.height,
  "--burst-x": CENTRE_BURST.x,
  "--burst-y": CENTRE_BURST.y,
  "--burst-rotate": CENTRE_BURST.rotate,
} as CSSProperties;

function CentreBurst() {
  return (
    <div className="pitch-burst" data-burst>
      <Burst className="pitch-burst__shape" seed={17}>
        <h1 className="pitch-burst__word">Call Kenji!</h1>
        <p className="pitch-burst__title">Kenji's Universe</p>
        <p className="pitch-burst__ja comic-ja" lang="ja">
          ケンジの世界
        </p>
      </Burst>
    </div>
  );
}

/** The whole universe: the burst in the middle, the doodle trail and the nine stops. */
export function PitchWorld({ ref, step, isCanvas, onJump }: PitchWorldProps) {
  const isOverview = step === OVERVIEW_STEP;
  const shownStop: StopId | null = STEPS[step - 1]?.stop ?? null;
  return (
    <div ref={ref} className="pitch-world" style={WORLD_STYLE}>
      <PitchConnectors />
      <CentreBurst />
      {STOPS.map((stop, index) => (
        <PitchStop
          key={stop.id}
          stop={stop}
          number={index + 1}
          isActive={!isCanvas || stop.id === shownStop}
          onFly={
            isCanvas && isOverview
              ? () => {
                  onJump(firstStepOf(stop.id));
                }
              : null
          }
        >
          <StopContent id={stop.id} />
        </PitchStop>
      ))}
    </div>
  );
}
