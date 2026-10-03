import type { ReactNode } from "react";
import { burstPoints, toSvgPoints } from "./burstShape.ts";

const BOX_WIDTH = 320;
const BOX_HEIGHT = 200;
const SHADOW_OFFSET = 10;
const MARGIN = 14;
const SPIKES = 15;
const INNER_RATIO = 0.74;
const WOBBLE = 0.1;
const VIEW_BOX = [-MARGIN, -MARGIN, BOX_WIDTH + MARGIN * 2, BOX_HEIGHT + MARGIN * 2].join(" ");
const SHADOW_SHIFT = `translate(${String(SHADOW_OFFSET)} ${String(SHADOW_OFFSET)})`;

interface BurstProps {
  children: ReactNode;
  seed?: number;
  className?: string;
}

/** The comic starburst from the reference: a white face, an ink outline and a red shadow. */
export function Burst({ children, seed = 3, className = "" }: BurstProps) {
  const outline = toSvgPoints(
    burstPoints({ spikes: SPIKES, innerRatio: INNER_RATIO, wobble: WOBBLE, seed }),
    BOX_WIDTH,
    BOX_HEIGHT,
  );
  return (
    <div className={`burst ${className}`}>
      <svg className="burst__shape" viewBox={VIEW_BOX} aria-hidden="true" focusable="false">
        <polygon className="burst__shadow" points={outline} transform={SHADOW_SHIFT} />
        <polygon className="burst__face" points={outline} />
      </svg>
      <div className="burst__content">{children}</div>
    </div>
  );
}
