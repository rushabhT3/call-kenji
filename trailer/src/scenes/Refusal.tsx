import { AbsoluteFill, Img, Sequence, interpolate, staticFile, useCurrentFrame } from "remotion";
import { Halftone } from "../effects.tsx";
import { TitleCard, local, useFade } from "../parts.tsx";
import { COLOR, FONT, frames, timeline } from "../theme.ts";

const START = timeline.scenes.refusal[0];
const { offer, sorry } = timeline.voice;
const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** A comic speech balloon whose words type on as the real voice says them. */
function Balloon({ who, ja, en, length, side, tone }: { who: string; ja: string; en: string; length: number; side: "left" | "right"; tone: string }) {
  const frame = useCurrentFrame();
  const opacity = useFade(length, 6, 10);
  const typed = Math.round(interpolate(frame, [4, length * 0.82], [0, ja.length], CLAMP));
  const rise = interpolate(frame, [0, 8], [40, 0], CLAMP);
  return (
    <AbsoluteFill style={{ alignItems: side === "left" ? "flex-start" : "flex-end", justifyContent: "center", padding: "0 150px", opacity }}>
      <div style={{ transform: `translateY(${rise}px) rotate(${side === "left" ? -1.5 : 1.5}deg)`, width: 1180 }}>
        <div
          style={{
            display: "inline-block",
            fontFamily: FONT.trailer,
            fontSize: 44,
            letterSpacing: "0.14em",
            color: COLOR.ink,
            background: tone,
            border: `5px solid ${COLOR.ink}`,
            borderRadius: 999,
            padding: "2px 26px",
            marginBottom: 18,
          }}
        >
          {who}
        </div>
        <div
          style={{
            position: "relative",
            background: COLOR.white,
            border: `7px solid ${COLOR.ink}`,
            borderRadius: 40,
            boxShadow: `16px 16px 0 ${COLOR.red}`,
            padding: "34px 46px",
          }}
        >
          <div style={{ fontFamily: FONT.ja, fontSize: 62, lineHeight: 1.45, color: COLOR.ink }}>
            {ja.slice(0, typed)}
            <span style={{ color: "transparent" }}>{ja.slice(typed)}</span>
          </div>
          <div style={{ fontFamily: FONT.subtitle, fontSize: 34, color: "#4a4243", marginTop: 14 }}>{en}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
}

function Behind() {
  const frame = useCurrentFrame();
  const drift = interpolate(frame, [0, frames(13)], [1.15, 1.3]);
  return (
    <AbsoluteFill style={{ background: COLOR.night }}>
      <AbsoluteFill style={{ transform: `scale(${drift})`, filter: "blur(10px) brightness(0.32) saturate(0.6)" }}>
        <Img src={staticFile("shots/card-transcript.webp")} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>
      <Halftone color={COLOR.red} opacity={0.1} />
    </AbsoluteFill>
  );
}

export function Refusal() {
  const offerLength = frames(offer.to - offer.from) + 6;
  const sorryLength = frames(sorry.to - sorry.from) + 6;
  const [cardIn, cardOut] = timeline.cards.cannotBreak;
  return (
    <AbsoluteFill>
      <Behind />
      <Sequence from={local(offer.at, START) - 4} durationInFrames={offerLength}>
        <Balloon who="THE CALLER" ja={offer.ja} en={offer.en} length={offerLength} side="left" tone={COLOR.paper} />
      </Sequence>
      <Sequence from={local(sorry.at, START) - 4} durationInFrames={sorryLength}>
        <Balloon who="KENJI" ja={sorry.ja} en={sorry.en} length={sorryLength} side="right" tone={COLOR.teal} />
      </Sequence>
      <Sequence from={local(cardIn, START)} durationInFrames={frames(cardOut - cardIn)}>
        <AbsoluteFill style={{ background: "radial-gradient(circle, rgba(214,75,64,0.55) 0%, rgba(10,8,8,0.96) 70%)" }} />
        <TitleCard text="IT CANNOT BREAK THE RULES." length={frames(cardOut - cardIn)} slam size={140} />
      </Sequence>
    </AbsoluteFill>
  );
}
