import type { ComponentType } from "react";
import { AbsoluteFill, Audio, Sequence, staticFile } from "remotion";
import { Flash, Grain, Letterbox, LightLeak, Shake, Vignette } from "./effects.tsx";
import { useFontsReady } from "./fonts.ts";
import { ColdOpen } from "./scenes/ColdOpen.tsx";
import { EndCard } from "./scenes/EndCard.tsx";
import { FlipBook } from "./scenes/FlipBook.tsx";
import { Logo } from "./scenes/Logo.tsx";
import { Montage } from "./scenes/Montage.tsx";
import { PromiseScene } from "./scenes/Promise.tsx";
import { Refusal } from "./scenes/Refusal.tsx";
import { Titles } from "./scenes/Titles.tsx";
import { VoiceReveal } from "./scenes/VoiceReveal.tsx";
import { frames, timeline } from "./theme.ts";

const SCENES: [keyof typeof timeline.scenes, ComponentType][] = [
  ["coldOpen", ColdOpen],
  ["voice", VoiceReveal],
  ["titles", Titles],
  ["montage", Montage],
  ["refusal", Refusal],
  ["flipbook", FlipBook],
  ["promise", PromiseScene],
  ["logo", Logo],
  ["endCard", EndCard],
];

export function Trailer() {
  useFontsReady();
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <Shake>
        {SCENES.map(([name, Scene]) => {
          const [from, to] = timeline.scenes[name];
          return (
            <Sequence key={name} name={name} from={frames(from)} durationInFrames={frames(to - from)}>
              <Scene />
            </Sequence>
          );
        })}
      </Shake>
      <LightLeak />
      <Vignette strength={0.7} />
      <Grain />
      <Flash />
      <Letterbox />
      <Audio src={staticFile("audio/soundtrack.wav")} />
    </AbsoluteFill>
  );
}
