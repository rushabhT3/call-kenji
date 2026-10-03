import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Halftone } from "../effects.tsx";
import { COLOR, FONT, frames, timeline } from "../theme.ts";
import { Doodles, LogoMark, Rays } from "./Logo.tsx";

const LENGTH = frames(timeline.scenes.endCard[1] - timeline.scenes.endCard[0]);
const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** The burst rises and shrinks; the call to action and the address land beneath it. */
export function EndCard() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const lift = spring({ frame, fps, config: { damping: 16, stiffness: 90 } });
  const title = spring({ frame: frame - 10, fps, config: { damping: 12, stiffness: 160 } });
  const url = spring({ frame: frame - 22, fps, config: { damping: 14, stiffness: 140 } });
  const credit = interpolate(frame, [38, 52], [0, 1], CLAMP);
  const out = interpolate(frame, [LENGTH - frames(1.6), LENGTH], [0, 1], CLAMP);
  return (
    <AbsoluteFill style={{ background: COLOR.paper, alignItems: "center" }}>
      <Rays turn={frame * 0.3 + 120} />
      <Halftone color={COLOR.orange} opacity={0.16} />
      <Doodles draw={1} />
      <div style={{ position: "absolute", top: interpolate(lift, [0, 1], [-30, -170]), transform: `scale(${interpolate(lift, [0, 1], [1, 0.56])})` }}>
        <LogoMark rotate={-2} textScale={0.86} />
      </div>
      <div
        style={{
          position: "absolute",
          top: 560,
          fontFamily: FONT.trailer,
          fontSize: 150,
          letterSpacing: "0.06em",
          color: COLOR.ink,
          textShadow: `8px 8px 0 ${COLOR.red}`,
          transform: `scale(${interpolate(title, [0, 1], [1.6, 1])})`,
          opacity: interpolate(title, [0, 0.3], [0, 1], CLAMP),
        }}
      >
        CALL HIM TODAY.
      </div>
      <div
        style={{
          position: "absolute",
          top: 760,
          fontFamily: FONT.subtitle,
          fontWeight: 500,
          fontSize: 50,
          color: COLOR.ink,
          background: COLOR.white,
          border: `6px solid ${COLOR.ink}`,
          borderRadius: 999,
          padding: "10px 46px",
          boxShadow: `10px 10px 0 ${COLOR.ink}`,
          transform: `translateY(${interpolate(url, [0, 1], [80, 0])}px)`,
          opacity: interpolate(url, [0, 0.3], [0, 1], CLAMP),
        }}
      >
        call-kenji.call-kenji-web.workers.dev
      </div>
      <div style={{ position: "absolute", top: 905, fontFamily: FONT.marker, fontSize: 46, color: COLOR.ink, opacity: credit }}>
        Built by Rushabh Trivedi
      </div>
      <AbsoluteFill style={{ background: "#000", opacity: out }} />
    </AbsoluteFill>
  );
}
