import { useAudioData, visualizeAudio } from "@remotion/media-utils";
import { AbsoluteFill, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { COLOR } from "../theme.ts";

const BARS = 64;

/** Kenji's real voice, drawn as it plays: a mirrored bar spectrum that glows in the dark. */
export function Waveform({ file, width = 1100, height = 220, opacity = 1 }: { file: string; width?: number; height?: number; opacity?: number }) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const audio = useAudioData(staticFile(file));
  if (!audio) {
    return null;
  }
  const levels = visualizeAudio({ fps, frame, audioData: audio, numberOfSamples: BARS, optimizeFor: "accuracy" });
  // Voice energy sits in the low bins; lifting each bin by its frequency spreads the bars out.
  const lifted = levels.map((level, bin) => Math.min(1, Math.max(0, Math.sqrt(level * (1 + bin * 0.22)) * 2.6 - 0.32)));
  const mirrored = [...lifted.slice().reverse(), ...lifted];
  const gap = 4;
  const barWidth = width / mirrored.length - gap;
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", opacity }}>
      <div style={{ display: "flex", alignItems: "center", gap, height, filter: `drop-shadow(0 0 18px ${COLOR.paper})` }}>
        {mirrored.map((level, index) => (
          <div
            key={index}
            style={{
              width: barWidth,
              height: Math.max(4, level * height),
              borderRadius: barWidth,
              background: `linear-gradient(180deg, ${COLOR.white}, ${COLOR.paper})`,
            }}
          />
        ))}
      </div>
    </AbsoluteFill>
  );
}
