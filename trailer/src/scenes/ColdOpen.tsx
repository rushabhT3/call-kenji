import { AbsoluteFill, Sequence, interpolate, useCurrentFrame } from "remotion";
import { TitleCard, local } from "../parts.tsx";
import { COLOR, frames, timeline } from "../theme.ts";

const START = timeline.scenes.coldOpen[0];

/** A single pulse of light at the centre on each clock tick, like a second hand in the dark. */
function TickPulse() {
  const frame = useCurrentFrame();
  const ticks = timeline.ticks.map((at) => local(at, START));
  const since = Math.min(...ticks.filter((at) => at <= frame).map((at) => frame - at), 999);
  const glow = Math.exp(-since / 6) * 0.22;
  return (
    <AbsoluteFill
      style={{ background: `radial-gradient(circle at 50% 50%, rgba(253,252,249,${glow}) 0%, transparent 40%)` }}
    />
  );
}

export function ColdOpen() {
  const [everyIn, everyOut] = timeline.cards.everyCall;
  const [silenceIn, silenceOut] = timeline.cards.hasSilence;
  const frame = useCurrentFrame();
  const drift = interpolate(frame, [0, frames(8.8)], [0, 1]);
  return (
    <AbsoluteFill style={{ background: COLOR.night }}>
      <TickPulse />
      <Sequence from={local(everyIn, START)} durationInFrames={frames(everyOut - everyIn)}>
        <TitleCard text="EVERY PHONE CALL…" length={frames(everyOut - everyIn)} size={150} />
      </Sequence>
      <Sequence from={local(silenceIn, START)} durationInFrames={frames(silenceOut - silenceIn)}>
        <TitleCard text="…HAS A SILENCE." length={frames(silenceOut - silenceIn)} size={150} />
      </Sequence>
      <AbsoluteFill style={{ background: `rgba(0,0,0,${0.2 * drift})` }} />
    </AbsoluteFill>
  );
}
