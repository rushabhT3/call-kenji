import { burstPoints, toSvgPoints } from "../showcase/burstShape.ts";
import { SHOWCASE_PATH } from "../showcase/route.ts";

const BOX_WIDTH = 100;
const BOX_HEIGHT = 50;
const SHADOW_OFFSET = 4;
const OUTLINE = toSvgPoints(
  burstPoints({ spikes: 14, innerRatio: 0.85, wobble: 0.08, seed: 5 }),
  BOX_WIDTH,
  BOX_HEIGHT,
);
const SHADOW_SHIFT = `translate(${String(SHADOW_OFFSET)} ${String(SHADOW_OFFSET)})`;
const SPARKS = ["1", "2", "3", "4"] as const;

function BurstBackdrop() {
  return (
    <svg
      className="features-link__burst"
      viewBox={`0 0 ${String(BOX_WIDTH)} ${String(BOX_HEIGHT)}`}
      preserveAspectRatio="none"
      aria-hidden="true"
      focusable="false"
    >
      <polygon className="features-link__shadow" points={OUTLINE} transform={SHADOW_SHIFT} />
      <polygon className="features-link__face" points={OUTLINE} />
    </svg>
  );
}

/**
 * The way to the features page. It starts as a plain link, sputters like a tube light, then is
 * plugged in: a blinding flash and sparks, as when the sign comes on in Dexter's Laboratory.
 */
export function FeaturesLink() {
  return (
    <a className="caption site-header__link features-link" href={SHOWCASE_PATH}>
      <span className="features-link__plain" aria-hidden="true">
        Features
      </span>
      <span className="features-link__lit">
        <span className="features-link__flash" aria-hidden="true" />
        <BurstBackdrop />
        <span className="features-link__word">Features</span>
        {SPARKS.map((spark) => (
          <span
            key={spark}
            className={`features-link__spark features-link__spark--${spark}`}
            aria-hidden="true"
          />
        ))}
      </span>
    </a>
  );
}
