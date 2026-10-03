import { AbsoluteFill, useCurrentFrame } from "remotion";
import { useFontsReady } from "./fonts.ts";
import { Doodles, LogoMark, Rays, Sparks } from "./scenes/Logo.tsx";
import { COLOR, FONT, HEIGHT, WIDTH } from "./theme.ts";

export const GIF_FRAMES = 135;
export const GIF_WIDTH = 600;
export const GIF_HEIGHT = 338;
const SCALE = GIF_WIDTH / WIDTH;

function PlayButton() {
  const frame = useCurrentFrame();
  const pulse = 1 + 0.06 * Math.sin((frame / GIF_FRAMES) * Math.PI * 4);
  return (
    <div
      style={{
        position: "absolute",
        right: 110,
        bottom: 100,
        display: "flex",
        alignItems: "center",
        gap: 34,
        transform: `scale(${pulse})`,
        transformOrigin: "right bottom",
      }}
    >
      <div style={{ fontFamily: FONT.trailer, fontSize: 96, color: COLOR.ink, letterSpacing: "0.06em", textShadow: `6px 6px 0 ${COLOR.white}` }}>
        WATCH THE TRAILER
      </div>
      <div
        style={{
          width: 240,
          height: 240,
          borderRadius: "50%",
          background: COLOR.red,
          border: `12px solid ${COLOR.ink}`,
          boxShadow: `14px 14px 0 ${COLOR.ink}`,
          display: "grid",
          placeItems: "center",
        }}
      >
        <div
          style={{
            width: 0,
            height: 0,
            borderTop: "58px solid transparent",
            borderBottom: "58px solid transparent",
            borderLeft: `96px solid ${COLOR.white}`,
            marginLeft: 26,
          }}
        />
      </div>
    </div>
  );
}

/**
 * The email teaser: the lit logo on comic paper, sparks flying, the play button pulsing.
 * The backdrop holds still, because a GIF pays for every pixel that changes; every motion repeats
 * within the loop, so the last frame meets the first.
 */
export function EmailGif() {
  useFontsReady();
  return (
    <AbsoluteFill style={{ background: COLOR.paper }}>
      <div style={{ position: "absolute", top: 0, left: 0, width: WIDTH, height: HEIGHT, transform: `scale(${SCALE})`, transformOrigin: "top left" }}>
        <Rays turn={0} />
        <Doodles draw={1} />
        <Sparks cycle={GIF_FRAMES / 3} />
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", paddingBottom: 150, paddingRight: 260 }}>
          <LogoMark scale={0.7} rotate={-3} textScale={0.86} />
        </AbsoluteFill>
        <PlayButton />
      </div>
    </AbsoluteFill>
  );
}
