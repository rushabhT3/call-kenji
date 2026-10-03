import { AbsoluteFill, Sequence } from "remotion";
import { Halftone } from "../effects.tsx";
import { TitleCard, local } from "../parts.tsx";
import { COLOR, FONT, frames, timeline } from "../theme.ts";

const START = timeline.scenes.titles[0];

function Card({ span, text, size, above }: { span: number[]; text: string; size?: number; above?: string }) {
  const length = frames(span[1] - span[0]);
  return (
    <Sequence from={local(span[0], START)} durationInFrames={length}>
      <TitleCard
        text={text}
        length={length}
        slam
        size={size}
        above={
          above ? (
            <div style={{ fontFamily: FONT.ja, fontSize: 64, color: COLOR.paper, marginBottom: 6, letterSpacing: "0.2em" }}>
              {above}
            </div>
          ) : undefined
        }
      />
    </Sequence>
  );
}

export function Titles() {
  const { voiceAgent, inJapanese, howItThinks } = timeline.cards;
  return (
    <AbsoluteFill style={{ background: COLOR.night }}>
      <Halftone color={COLOR.red} opacity={0.07} />
      <Card span={voiceAgent} text="A VOICE AGENT" size={210} />
      <Card span={inJapanese} text="IN JAPANESE" size={210} above="日本語で" />
      <Card span={howItThinks} text="THAT SHOWS YOU HOW IT THINKS." size={128} />
    </AbsoluteFill>
  );
}
