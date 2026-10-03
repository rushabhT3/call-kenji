import type { ReactNode } from "react";
import { AbsoluteFill, Sequence, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Halftone } from "../effects.tsx";
import { Caption, Panel, local } from "../parts.tsx";
import { COLOR, FONT, frames, timeline } from "../theme.ts";

const START = timeline.scenes.montage[0];
const END = timeline.scenes.montage[1];
const BEATS = timeline.montage;
const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
// The top of each safeguard's row on the compliance card as the montage frames it.
const STAMP_ROWS = [360, 482, 570, 658, 746];

/** A beat of the montage: snaps in on its whoosh with a punch of scale, drifts while it holds. */
function Beat({ from, to, children }: { from: number; to: number; children: ReactNode }) {
  return (
    <Sequence from={local(from, START)} durationInFrames={frames(to - from)}>
      <Punch length={frames(to - from)}>{children}</Punch>
    </Sequence>
  );
}

function Punch({ length, children }: { length: number; children: ReactNode }) {
  const frame = useCurrentFrame();
  const scale = interpolate(frame, [0, 4, length], [1.22, 1, 1.05], CLAMP);
  const blur = interpolate(frame, [0, 4], [10, 0], CLAMP);
  return <AbsoluteFill style={{ transform: `scale(${scale})`, filter: `blur(${blur}px)` }}>{children}</AbsoluteFill>;
}

function Split({ src, width, caption, flip = false }: { src: string; width: number; caption: ReactNode; flip?: boolean }) {
  return (
    <AbsoluteFill
      style={{
        flexDirection: flip ? "row-reverse" : "row",
        alignItems: "center",
        justifyContent: "center",
        gap: 90,
        padding: "0 120px",
      }}
    >
      <Panel src={src} width={width} style={{ transform: `rotate(${flip ? 2.5 : -2.5}deg)` }} />
      <Caption style={{ maxWidth: 640, textAlign: flip ? "right" : "left" }}>{caption}</Caption>
    </AbsoluteFill>
  );
}

function Stamp({ at, index }: { at: number; index: number }) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const land = local(at, BEATS.compliance);
  const pop = spring({ frame: frame - land, fps, config: { damping: 11, stiffness: 220 } });
  if (frame < land) {
    return null;
  }
  return (
    <div
      style={{
        position: "absolute",
        left: 1300,
        top: STAMP_ROWS[index],
        transform: `scale(${interpolate(pop, [0, 1], [3, 1])}) rotate(${-9 + index * 4}deg)`,
        opacity: interpolate(pop, [0, 0.4], [0, 1], CLAMP),
        fontFamily: FONT.trailer,
        fontSize: 62,
        letterSpacing: "0.08em",
        color: COLOR.green,
        border: `6px solid ${COLOR.green}`,
        borderRadius: 14,
        padding: "0 22px",
        lineHeight: 1.1,
        background: "rgba(253,252,249,0.9)",
        boxShadow: "0 10px 30px rgba(0,0,0,0.45)",
      }}
    >
      PASS
    </div>
  );
}

function Compliance() {
  return (
    <AbsoluteFill>
      <Split src="shots/card-compliance.webp" width={600} caption={<>THE LAW,<br />CHECKED LIVE.</>} flip />
      {BEATS.stamps.map((at, index) => (
        <Stamp key={at} at={at} index={index} />
      ))}
    </AbsoluteFill>
  );
}

/** A number slammed full-screen in comic lettering, with a red-and-teal print offset. */
function Slam({ number, over, under, color = COLOR.paper }: { number: string; over: string; under?: string; color?: string }) {
  const frame = useCurrentFrame();
  const spread = interpolate(frame, [0, 6], [26, 6], CLAMP);
  const face = {
    position: "absolute" as const,
    fontFamily: FONT.trailer,
    fontSize: 400,
    lineHeight: 1,
    letterSpacing: "0.02em",
  };
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <Caption style={{ position: "absolute", top: 165, fontSize: 80, textShadow: `5px 5px 0 ${COLOR.ink}` }}>{over}</Caption>
      <div style={{ ...face, color: COLOR.teal, transform: `translate(${-spread}px, ${spread / 2}px)`, opacity: 0.8 }}>{number}</div>
      <div style={{ ...face, color: COLOR.red, transform: `translate(${spread}px, ${-spread / 2}px)`, opacity: 0.85 }}>{number}</div>
      <div style={{ ...face, color, WebkitTextStroke: `10px ${COLOR.ink}`, paintOrder: "stroke" }}>{number}</div>
      {under ? (
        <Caption style={{ position: "absolute", bottom: 160, fontSize: 70, textShadow: `5px 5px 0 ${COLOR.ink}` }}>{under}</Caption>
      ) : null}
    </AbsoluteFill>
  );
}

function Backdrop() {
  const frame = useCurrentFrame();
  const hue = interpolate(frame, [0, frames(END - START)], [0, 1]);
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 50% 45%, rgba(214,75,64,${0.25 + 0.2 * hue}) 0%, ${COLOR.night} 70%)`,
      }}
    >
      <Halftone color={COLOR.red} opacity={0.12} />
    </AbsoluteFill>
  );
}

export function Montage() {
  return (
    <AbsoluteFill>
      <Backdrop />
      <Beat from={BEATS.turn} to={BEATS.strategist}>
        <Split src="shots/card-turn.webp" width={860} caption={<>IT HEARS WHEN<br />YOU'VE FINISHED.</>} />
      </Beat>
      <Beat from={BEATS.strategist} to={BEATS.compliance}>
        <Split src="shots/card-strategist.webp" width={520} caption={<>A SECOND BRAIN<br />PLANS THE NEXT MOVE.</>} />
      </Beat>
      <Beat from={BEATS.compliance} to={BEATS.latency}>
        <Compliance />
      </Beat>
      <Beat from={BEATS.latency} to={BEATS.slowModel}>
        <Split src="shots/card-latency.webp" width={500} caption={<>EVERY MILLISECOND,<br />ON SCREEN.</>} flip />
      </Beat>
      <Beat from={BEATS.slowModel} to={BEATS.fastKenji}>
        <Slam number="2–6 SEC" over="THE MODEL THINKS FOR" color={COLOR.white} />
      </Beat>
      <Beat from={BEATS.fastKenji} to={BEATS.evals}>
        <Slam number="0.7 SEC" over="KENJI ANSWERS IN" under="(P50, REAL CALLS)" />
      </Beat>
      <Beat from={BEATS.evals} to={BEATS.coverage}>
        <Slam number="24/24" over="REAL-MODEL CONVERSATIONS" under="PASSED" color={COLOR.white} />
      </Beat>
      <Beat from={BEATS.coverage} to={END}>
        <Slam number="100%" over="EVERY RULE TESTED" under="LINE AND BRANCH" />
      </Beat>
    </AbsoluteFill>
  );
}
