import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { Halftone } from "../effects.tsx";
import { COLOR, frames, timeline } from "../theme.ts";

export const PAGES = [
  "shots/xray-desktop.webp",
  "shots/card-strategist.webp",
  "shots/live-1440.png",
  "shots/card-compliance.webp",
  "shots/before-call-1440.png",
  "shots/card-latency.webp",
  "shots/after-call-1440.png",
  "shots/card-transcript.webp",
  "shots/xray-phone.webp",
  "shots/card-turn.webp",
];

const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const TINTS = [COLOR.red, COLOR.paper, COLOR.orange, COLOR.teal];

/** When each page flips, in frames: slow at first, then faster and faster, like a thumb on a flip-book. */
export function flipSchedule(length: number): number[] {
  const times: number[] = [];
  let at = 0;
  let gap = 16;
  while (at < length) {
    times.push(at);
    at += Math.max(2, Math.round(gap));
    gap *= 0.86;
  }
  return times;
}

/** One comic page: a real screenshot on white paper with an ink frame. */
export function Page({ src, tint }: { src: string; tint: string }) {
  return (
    <div
      style={{
        position: "absolute",
        inset: "150px 340px",
        background: COLOR.white,
        border: `8px solid ${COLOR.ink}`,
        borderRadius: 18,
        overflow: "hidden",
        boxShadow: "0 30px 60px rgba(0,0,0,0.55)",
      }}
    >
      <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "top center", filter: "contrast(1.18) saturate(1.25)" }} />
      <div style={{ position: "absolute", inset: 0, background: tint, mixBlendMode: "multiply", opacity: 0.22 }} />
      <Halftone color={COLOR.ink} opacity={0.14} />
    </div>
  );
}

/** Pages turning down over the top edge, faster and faster, all graded comic red and yellow. */
export function FlipBook({ length = frames(timeline.flipbook.end - timeline.flipbook.start) }: { length?: number }) {
  const frame = useCurrentFrame();
  const times = flipSchedule(length);
  const current = Math.max(0, times.filter((at) => at <= frame).length - 1);
  const flipLength = Math.max(2, (times[current + 1] ?? length) - times[current]);
  const turn = interpolate(frame - times[current], [0, flipLength * 0.8], [0, -112], CLAMP);
  const zoom = interpolate(frame, [0, length], [0.92, 1.3]);
  const heat = interpolate(frame, [length * 0.6, length], [0, 0.5], CLAMP);
  const blur = interpolate(frame, [length * 0.75, length], [0, 6], CLAMP);
  const page = (offset: number) => PAGES[(current + offset) % PAGES.length];
  const tint = (offset: number) => TINTS[(current + offset) % TINTS.length];
  return (
    <AbsoluteFill style={{ background: COLOR.red, perspective: 2200 }}>
      <Halftone color={COLOR.ink} opacity={0.25} />
      <AbsoluteFill style={{ transform: `scale(${zoom})`, filter: `blur(${blur}px)` }}>
        <AbsoluteFill style={{ transform: "translate(34px, 30px) rotate(3deg)" }}>
          <Page src={page(3)} tint={tint(3)} />
        </AbsoluteFill>
        <AbsoluteFill style={{ transform: "translate(18px, 16px) rotate(1.5deg)" }}>
          <Page src={page(2)} tint={tint(2)} />
        </AbsoluteFill>
        <Page src={page(1)} tint={tint(1)} />
        <AbsoluteFill style={{ transformOrigin: "50% 8%", transform: `rotateX(${turn}deg)`, backfaceVisibility: "hidden" }}>
          <Page src={page(0)} tint={tint(0)} />
          <AbsoluteFill style={{ background: `rgba(0,0,0,${interpolate(-turn, [0, 112], [0, 0.55])})` }} />
        </AbsoluteFill>
      </AbsoluteFill>
      <AbsoluteFill style={{ background: COLOR.white, opacity: heat, mixBlendMode: "screen" }} />
    </AbsoluteFill>
  );
}
