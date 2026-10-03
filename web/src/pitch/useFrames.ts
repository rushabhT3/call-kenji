import { useLayoutEffect, useState } from "react";
import type { Frame } from "./camera.ts";
import { sizeOf } from "./flight.ts";
import { measureFrames } from "./measure.ts";
import type { CameraRefs } from "./useCamera.ts";

/** Every step's pages, measured once laid out and again whenever the window or the fonts change. */
export function useFrames(refs: CameraRefs, isCanvas: boolean): Frame[][] | null {
  const [frames, setFrames] = useState<Frame[][] | null>(null);

  useLayoutEffect(() => {
    const viewport = refs.viewport.current;
    const world = refs.world.current;
    if (!isCanvas || !viewport || !world) {
      return;
    }
    const measure = () => {
      setFrames(measureFrames(world, sizeOf(viewport)));
    };
    // The observer's first report, as soon as it starts, takes the first measurement.
    const observer = new ResizeObserver(measure);
    observer.observe(viewport);
    document.fonts.addEventListener("loadingdone", measure);
    return () => {
      observer.disconnect();
      document.fonts.removeEventListener("loadingdone", measure);
    };
  }, [refs, isCanvas]);

  return isCanvas ? frames : null;
}
