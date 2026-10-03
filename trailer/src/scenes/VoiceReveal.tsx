import { AbsoluteFill, Img, Sequence, interpolate, staticFile, useCurrentFrame } from "remotion";
import { Panel, Subtitle, local } from "../parts.tsx";
import { COLOR, frames, timeline } from "../theme.ts";
import { Waveform } from "./Waveform.tsx";

const START = timeline.scenes.voice[0];
const END = timeline.scenes.voice[1];
const HELLO = timeline.voice.hello;
const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** The X-ray rising out of the dark, the camera dollying across it, two cards floating in front. */
function Dolly() {
  const frame = useCurrentFrame();
  const length = frames(END - START);
  const reveal = interpolate(frame, [frames(1.2), frames(4.5)], [0, 1], CLAMP);
  const light = interpolate(frame, [frames(1.2), frames(7)], [0.35, 0.95], CLAMP);
  const scale = interpolate(frame, [0, length], [1.42, 1.12]);
  const x = interpolate(frame, [0, length], [7, -6]);
  const tilt = interpolate(frame, [0, length], [10, -4]);
  const cards = interpolate(frame, [frames(5.4), frames(7.4)], [0, 1], CLAMP);
  return (
    <AbsoluteFill style={{ perspective: 1800, opacity: reveal }}>
      <AbsoluteFill
        style={{
          transform: `translateX(${x}%) scale(${scale}) rotateY(${tilt}deg)`,
          filter: `brightness(${light}) contrast(1.12) saturate(0.85)`,
        }}
      >
        <Img src={staticFile("shots/xray-desktop.webp")} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(10,8,8,0.85) 0%, transparent 35%, transparent 65%, rgba(10,8,8,0.85) 100%)" }} />
      <div
        style={{
          position: "absolute",
          left: 120,
          top: 250,
          opacity: cards,
          transform: `translate3d(${interpolate(frame, [0, length], [80, -60])}px, ${interpolate(cards, [0, 1], [60, 0])}px, 0) rotate(-4deg)`,
        }}
      >
        <Panel src="shots/card-turn.webp" width={620} />
      </div>
      <div
        style={{
          position: "absolute",
          right: 140,
          top: 170,
          opacity: cards,
          transform: `translate3d(${interpolate(frame, [0, length], [-40, 90])}px, ${interpolate(cards, [0, 1], [-50, 0])}px, 0) rotate(3deg)`,
        }}
      >
        <Panel src="shots/card-strategist.webp" width={430} shadow={COLOR.orange} />
      </div>
    </AbsoluteFill>
  );
}

export function VoiceReveal() {
  const helloLength = frames(HELLO.to - HELLO.from);
  return (
    <AbsoluteFill style={{ background: COLOR.night }}>
      <Dolly />
      <Sequence from={local(HELLO.at, START)} durationInFrames={helloLength}>
        <Waveform file={HELLO.file} width={900} height={170} opacity={0.9} />
        <Subtitle ja={HELLO.ja} en={HELLO.en} length={helloLength} />
      </Sequence>
    </AbsoluteFill>
  );
}
