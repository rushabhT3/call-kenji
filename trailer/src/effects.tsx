import type { CSSProperties, ReactNode } from "react";
import { AbsoluteFill, interpolate, random, useCurrentFrame } from "remotion";
import { COLOR, LETTERBOX, frames, timeline } from "./theme.ts";

const HIT_FRAMES = [
  ...timeline.braams,
  ...timeline.hits,
  ...timeline.slams,
  timeline.impact,
].map(frames);
const SLAM_FRAMES = [...timeline.braams, ...timeline.slams, timeline.impact].map(frames);

function sinceLast(frame: number, events: number[]): number {
  const past = events.filter((at) => at <= frame);
  return past.length ? frame - Math.max(...past) : Number.POSITIVE_INFINITY;
}

/** Camera shake that kicks on every slam and settles within a few frames. */
export function Shake({ children }: { children: ReactNode }) {
  const frame = useCurrentFrame();
  const since = sinceLast(frame, SLAM_FRAMES);
  const strength = since === Number.POSITIVE_INFINITY ? 0 : 26 * Math.exp(-since / 5);
  const x = (random(`x${frame}`) - 0.5) * strength;
  const y = (random(`y${frame}`) - 0.5) * strength;
  return <AbsoluteFill style={{ transform: `translate(${x}px, ${y}px)` }}>{children}</AbsoluteFill>;
}

/** A white flash on every hit; the final impact flashes longest. */
export function Flash() {
  const frame = useCurrentFrame();
  const since = sinceLast(frame, HIT_FRAMES);
  const sinceImpact = frame - frames(timeline.impact);
  const impactGlow = sinceImpact >= 0 ? Math.exp(-sinceImpact / 7) : 0;
  const hitGlow = since === Number.POSITIVE_INFINITY ? 0 : 0.35 * Math.exp(-since / 2.5);
  const opacity = Math.max(impactGlow, hitGlow);
  return <AbsoluteFill style={{ background: COLOR.white, opacity, mixBlendMode: "screen" }} />;
}

export function Grain() {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ opacity: 0.09, mixBlendMode: "overlay", pointerEvents: "none" }}>
      <svg width="100%" height="100%">
        <filter id={`grain-${frame % 6}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed={frame % 6} />
        </filter>
        <rect width="100%" height="100%" filter={`url(#grain-${frame % 6})`} />
      </svg>
    </AbsoluteFill>
  );
}

export function Vignette({ strength = 0.75 }: { strength?: number }) {
  const frame = useCurrentFrame();
  const after = interpolate(frame, [frames(timeline.impact), frames(timeline.impact) + 8], [strength, 0.28], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(ellipse at center, transparent 45%, rgba(0,0,0,${after}) 100%)`,
        pointerEvents: "none",
      }}
    />
  );
}

/** Cinema bars, which slide away when the logo lands. */
export function Letterbox() {
  const frame = useCurrentFrame();
  const open = interpolate(frame, [frames(timeline.impact), frames(timeline.impact) + 10], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const bar: CSSProperties = { position: "absolute", left: 0, right: 0, height: LETTERBOX * open, background: "#000" };
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div style={{ ...bar, top: 0 }} />
      <div style={{ ...bar, bottom: 0 }} />
    </AbsoluteFill>
  );
}

/** A warm lens flare that blooms on each hit, from the side. */
export function LightLeak() {
  const frame = useCurrentFrame();
  const since = sinceLast(frame, SLAM_FRAMES);
  const glow = since === Number.POSITIVE_INFINITY ? 0 : Math.exp(-since / 9);
  const side = random(`leak${frame - since}`) > 0.5 ? "12%" : "88%";
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at ${side} 40%, rgba(232,149,79,${0.55 * glow}) 0%, rgba(214,75,64,${0.3 * glow}) 25%, transparent 55%)`,
        mixBlendMode: "screen",
        pointerEvents: "none",
      }}
    />
  );
}

/** Comic halftone dots, for the comic-coloured scenes. */
export function Halftone({ color = COLOR.red, opacity = 0.18 }: { color?: string; opacity?: number }) {
  return (
    <AbsoluteFill
      style={{
        backgroundImage: `radial-gradient(${color} 22%, transparent 24%)`,
        backgroundSize: "18px 18px",
        opacity,
        pointerEvents: "none",
      }}
    />
  );
}
