import type { ReactNode } from "react";
import { COLOR } from "./theme.ts";

// The starburst outline from web/src/showcase/burstShape.ts, so the trailer's logo is the site's.
function seededRandom(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let mixed = Math.imul(state ^ (state >>> 15), 1 | state);
    mixed = (mixed + Math.imul(mixed ^ (mixed >>> 7), 61 | mixed)) ^ mixed;
    return ((mixed ^ (mixed >>> 14)) >>> 0) / 2 ** 32;
  };
}

function outline(spikes: number, innerRatio: number, wobble: number, seed: number, w: number, h: number): string {
  const random = seededRandom(seed);
  const step = (Math.PI * 2) / (spikes * 2);
  return Array.from({ length: spikes * 2 }, (_, index) => {
    const base = index % 2 === 0 ? 1 : innerRatio;
    const radius = base * (1 - wobble * random());
    const angle = index * step + (random() - 0.5) * step * wobble * 2;
    return `${((Math.cos(angle) * radius + 1) * w) / 2},${((Math.sin(angle) * radius + 1) * h) / 2}`;
  }).join(" ");
}

const W = 320;
const H = 200;
const POINTS = outline(15, 0.74, 0.1, 11, W, H);

export function Starburst({ width, children, stroke = 7 }: { width: number; children?: ReactNode; stroke?: number }) {
  return (
    <div style={{ position: "relative", width, aspectRatio: "348 / 228", display: "grid", placeItems: "center" }}>
      <svg viewBox="-14 -14 348 228" style={{ position: "absolute", inset: 0, width: "100%", height: "100%", overflow: "visible" }}>
        <polygon points={POINTS} fill={COLOR.red} transform="translate(12 12)" />
        <polygon points={POINTS} fill={COLOR.white} stroke={COLOR.ink} strokeWidth={stroke} strokeLinejoin="round" />
      </svg>
      <div style={{ position: "relative", textAlign: "center" }}>{children}</div>
    </div>
  );
}
