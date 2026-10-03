import { AbsoluteFill, Sequence } from "remotion";
import { Subtitle, local } from "../parts.tsx";
import { COLOR, frames, timeline } from "../theme.ts";
import { Waveform } from "./Waveform.tsx";

const START = timeline.scenes.promise[0];
const PROMISE = timeline.voice.promise;

/** The trailer's held breath: black, silence, then Kenji alone. */
export function PromiseScene() {
  const length = frames(PROMISE.to - PROMISE.from);
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <Sequence from={local(PROMISE.at, START)} durationInFrames={length}>
        <Waveform file={PROMISE.file} width={760} height={130} opacity={0.85} />
        <Subtitle ja={PROMISE.ja} en={PROMISE.en} length={length} />
      </Sequence>
      <AbsoluteFill style={{ boxShadow: `inset 0 0 220px ${COLOR.night}` }} />
    </AbsoluteFill>
  );
}
