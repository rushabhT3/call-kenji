import type { CSSProperties, ReactNode } from "react";
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { COLOR, FONT, LETTERBOX, frames } from "./theme.ts";

const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** Fades in, holds, fades out over a sequence of the given length (frames are local). */
export function useFade(length: number, fadeIn = 10, fadeOut = 12): number {
  const frame = useCurrentFrame();
  return interpolate(frame, [0, fadeIn, length - fadeOut, length], [0, 1, 1, 0], CLAMP);
}

const METAL: CSSProperties = {
  backgroundImage: "linear-gradient(180deg, #ffffff 0%, #f1f1ef 38%, #a9adb5 62%, #e9e9e6 100%)",
  WebkitBackgroundClip: "text",
  backgroundClip: "text",
  color: "transparent",
  filter: "drop-shadow(0 0 24px rgba(255,255,255,0.25)) drop-shadow(0 6px 0 rgba(0,0,0,0.6))",
};

/** A trailer title card: chrome capitals that push in slowly; slammed cards hit from big. */
export function TitleCard({
  text,
  length,
  slam = false,
  size = 168,
  above,
}: {
  text: string;
  length: number;
  slam?: boolean;
  size?: number;
  above?: ReactNode;
}) {
  const frame = useCurrentFrame();
  const opacity = useFade(length, slam ? 1 : 14, 10);
  const enter = slam ? interpolate(frame, [0, 5], [1.7, 1], CLAMP) : 1;
  const push = interpolate(frame, [0, length], [1, 1.07]);
  const blur = slam ? interpolate(frame, [0, 5], [14, 0], CLAMP) : 0;
  const spacing = interpolate(frame, [0, length], [0.16, 0.08]);
  const sweep = interpolate(frame, [0, length], [-40, 140]);
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", opacity }}>
      <div style={{ transform: `scale(${enter * push})`, filter: `blur(${blur}px)`, textAlign: "center" }}>
        {above}
        <div
          style={{
            ...METAL,
            fontFamily: FONT.trailer,
            fontSize: size,
            letterSpacing: `${spacing}em`,
            lineHeight: 1,
            maskImage: `linear-gradient(100deg, rgba(0,0,0,0.78) ${sweep - 30}%, #000 ${sweep}%, rgba(0,0,0,0.78) ${sweep + 30}%)`,
          }}
        >
          {text}
        </div>
      </div>
    </AbsoluteFill>
  );
}

/** Dialogue subtitles: the Japanese as spoken, the English under it. */
export function Subtitle({ ja, en, length }: { ja: string; en: string; length: number }) {
  const opacity = useFade(length, 8, 10);
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: LETTERBOX + 34, opacity }}>
      <div
        style={{
          fontFamily: FONT.ja,
          fontSize: 44,
          whiteSpace: "nowrap",
          color: COLOR.white,
          textShadow: "0 3px 14px rgba(0,0,0,0.9)",
          letterSpacing: "0.04em",
          marginBottom: 10,
          textAlign: "center",
        }}
      >
        {ja}
      </div>
      <div
        style={{
          fontFamily: FONT.subtitle,
          fontSize: 32,
          color: "rgba(253,252,249,0.82)",
          textShadow: "0 2px 10px rgba(0,0,0,0.9)",
          letterSpacing: "0.03em",
        }}
      >
        {en}
      </div>
    </AbsoluteFill>
  );
}

/** A real screenshot framed as a comic panel: white mat, ink outline, red offset shadow. */
export function Panel({
  src,
  width,
  style,
  shadow = COLOR.red,
}: {
  src: string;
  width: number;
  style?: CSSProperties;
  shadow?: string;
}) {
  return (
    <div
      style={{
        width,
        padding: 14,
        background: COLOR.white,
        border: `6px solid ${COLOR.ink}`,
        borderRadius: 26,
        boxShadow: `18px 18px 0 ${shadow}`,
        ...style,
      }}
    >
      <Img src={staticFile(src)} style={{ width: "100%", display: "block", borderRadius: 14 }} />
    </div>
  );
}

/** A short caption in trailer capitals, for montage beats. */
export function Caption({ children, style }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <div
      style={{
        fontFamily: FONT.trailer,
        fontSize: 92,
        lineHeight: 0.95,
        color: COLOR.white,
        letterSpacing: "0.05em",
        textShadow: `6px 6px 0 ${COLOR.red}, 0 0 30px rgba(0,0,0,0.6)`,
        ...style,
      }}
    >
      {children}
    </div>
  );
}

/** Local seconds to frames within a sequence that starts at `start` seconds. */
export const local = (at: number, start: number): number => frames(at) - frames(start);
