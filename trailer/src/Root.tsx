import { Composition } from "remotion";
import { EmailGif, GIF_FRAMES, GIF_HEIGHT, GIF_WIDTH } from "./EmailGif.tsx";
import { DURATION_FRAMES, FPS, HEIGHT, WIDTH } from "./theme.ts";
import { Trailer } from "./Trailer.tsx";

export function RemotionRoot() {
  return (
    <>
      <Composition id="Trailer" component={Trailer} durationInFrames={DURATION_FRAMES} fps={FPS} width={WIDTH} height={HEIGHT} />
      <Composition id="EmailGif" component={EmailGif} durationInFrames={GIF_FRAMES} fps={FPS} width={GIF_WIDTH} height={GIF_HEIGHT} />
    </>
  );
}
