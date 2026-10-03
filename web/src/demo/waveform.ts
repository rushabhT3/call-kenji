import type WaveSurfer from "wavesurfer.js";

const BAR_WIDTH_PX = 2;
const BAR_GAP_PX = 1;
const BAR_RADIUS_PX = 1;
const CURSOR_WIDTH_PX = 2;

/** A colour the stylesheet sets on the container, so the canvas keeps to the design tokens. */
function tokenColour(container: HTMLElement, property: string): string {
  const colour = getComputedStyle(container).getPropertyValue(property).trim();
  if (colour === "") {
    throw new Error(`the waveform's container sets no ${property}`);
  }
  return colour;
}

/**
 * Draws the recording's waveform into the container and loads its sound, paused at the start.
 * The page's own position slider takes the clicks and drags, so the waveform takes none. The
 * library is fetched here, so only the demo's visitors download it.
 */
export async function createWaveform(container: HTMLElement, url: string): Promise<WaveSurfer> {
  const library = await import("wavesurfer.js");
  return library.default.create({
    container,
    url,
    height: "auto",
    waveColor: tokenColour(container, "--waveform-wave"),
    progressColor: tokenColour(container, "--waveform-played"),
    cursorColor: tokenColour(container, "--waveform-cursor"),
    cursorWidth: CURSOR_WIDTH_PX,
    barWidth: BAR_WIDTH_PX,
    barGap: BAR_GAP_PX,
    barRadius: BAR_RADIUS_PX,
    normalize: true,
    interact: false,
    hideScrollbar: true,
  });
}
