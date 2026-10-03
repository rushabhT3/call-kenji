import { AbsoluteFill, interpolate, random, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Starburst } from "../burst.tsx";
import { Halftone } from "../effects.tsx";
import { COLOR, FONT } from "../theme.ts";

const SPARK_COLORS = [COLOR.orange, COLOR.blue, COLOR.white, COLOR.red, COLOR.teal];
const SPARKS = Array.from({ length: 72 }, (_, index) => ({
  angle: random(`angle${index}`) * Math.PI * 2,
  speed: 520 + random(`speed${index}`) * 900,
  size: 26 + random(`size${index}`) * 58,
  spin: (random(`spin${index}`) - 0.5) * 720,
  color: SPARK_COLORS[index % SPARK_COLORS.length],
  delay: random(`delay${index}`) * 6,
}));
const STAR = "polygon(50% 0, 62% 38%, 100% 50%, 62% 62%, 50% 100%, 38% 62%, 0 50%, 38% 38%)";
const DOODLES = [
  { color: COLOR.orange, d: "M-40 130 C 120 40, 240 260, 420 150 S 660 30, 800 130" },
  { color: COLOR.teal, d: "M-60 900 C 90 790, 220 1040, 420 950" },
  { color: COLOR.green, d: "M1380 90 C 1540 20, 1660 220, 1840 160 S 2000 80, 2060 170" },
  { color: COLOR.blue, d: "M1460 920 C 1600 820, 1760 1020, 1980 930" },
];
const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** Sparks thrown out from the centre when the sign is switched on. `cycle` loops them for the email GIF. */
export function Sparks({ cycle }: { cycle?: number }) {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      {SPARKS.map((spark, index) => {
        const raw = frame - spark.delay;
        const t = cycle ? (((raw % cycle) + cycle) % cycle) / 30 : raw / 30;
        if (t < 0) {
          return null;
        }
        const travel = spark.speed * (1 - Math.exp(-t * 2.4));
        const fade = interpolate(t, [0, 0.1, 1.1, 1.6], [0, 1, 1, 0], CLAMP);
        return (
          <div
            key={index}
            style={{
              position: "absolute",
              width: spark.size,
              height: spark.size,
              background: spark.color,
              clipPath: STAR,
              opacity: fade,
              transform: `translate(${Math.cos(spark.angle) * travel}px, ${Math.sin(spark.angle) * travel * 0.62}px) rotate(${spark.spin * t}deg)`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
}

/** Light rays turning behind the burst; twelve-fold, so a 30° turn loops seamlessly. */
export function Rays({ turn }: { turn: number }) {
  return (
    <AbsoluteFill
      style={{
        background: `repeating-conic-gradient(from ${turn}deg at 50% 50%, rgba(253,252,249,0.55) 0deg 9deg, transparent 9deg 30deg)`,
        maskImage: "radial-gradient(circle at 50% 50%, #000 0%, transparent 72%)",
      }}
    />
  );
}

export function Doodles({ draw }: { draw: number }) {
  return (
    <svg viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
      {DOODLES.map((line) => (
        <path
          key={line.d}
          d={line.d}
          fill="none"
          stroke={line.color}
          strokeWidth={14}
          strokeLinecap="round"
          pathLength={1}
          strokeDasharray={1}
          strokeDashoffset={1 - draw}
        />
      ))}
    </svg>
  );
}

/**
 * The burst with its lettering. Drawn small, the marker face renders a little wider, so small
 * uses shrink the lettering a touch (`textScale`) to keep it inside the burst's valleys.
 */
export function LogoMark({ scale = 1, rotate = 0, textScale = 1 }: { scale?: number; rotate?: number; textScale?: number }) {
  return (
    <div style={{ transform: `scale(${scale}) rotate(${rotate}deg)` }}>
      <Starburst width={1240} stroke={6}>
        <div
          style={{
            fontFamily: FONT.marker,
            fontSize: 178 * textScale,
            lineHeight: 0.95,
            color: COLOR.ink,
            textTransform: "uppercase",
            letterSpacing: "-0.01em",
          }}
        >
          Call
          <br />
          Kenji!
        </div>
        <div style={{ fontFamily: FONT.ja, fontSize: 58 * textScale, color: COLOR.ink, marginTop: 6 * textScale, letterSpacing: "0.1em" }}>
          ケンジに電話
        </div>
      </Starburst>
    </div>
  );
}

/** The sign comes on: comic paper, the burst exploding in on a spring, rays, doodles and sparks. */
export function Logo() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame, fps, config: { damping: 9, stiffness: 130, mass: 0.9 } });
  const breathe = 1 + 0.015 * Math.sin(frame / 9);
  return (
    <AbsoluteFill style={{ background: COLOR.paper, alignItems: "center", justifyContent: "center" }}>
      <Rays turn={frame * 0.4} />
      <Halftone color={COLOR.orange} opacity={0.18} />
      <Doodles draw={interpolate(frame, [4, 34], [0, 1], CLAMP)} />
      <Sparks />
      <LogoMark scale={interpolate(pop, [0, 1], [0.05, 1]) * breathe} rotate={interpolate(pop, [0, 1], [-18, -2])} />
    </AbsoluteFill>
  );
}
