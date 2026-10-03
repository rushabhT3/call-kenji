import { useGSAP } from "@gsap/react";
import { gsap } from "gsap";
import { useRef, type RefObject } from "react";
import type { Frame } from "./camera.ts";
import { fly, intro, place, release, type CameraParts } from "./flight.ts";

gsap.registerPlugin(useGSAP);

export interface CameraRefs {
  viewport: RefObject<HTMLDivElement | null>;
  camera: RefObject<HTMLDivElement | null>;
  world: RefObject<HTMLDivElement | null>;
}

/** Where the camera is aimed, and the flight taking it there. */
interface Shot {
  frame: Frame | null;
  key: string | null;
  flight: gsap.core.Animation | null;
}

interface Aim {
  frame: Frame | null;
  /** Changes when the reader moves; a new frame with the same key is the same shot, re-measured. */
  key: string;
}

function partsOf(refs: CameraRefs): CameraParts | null {
  const [viewport, camera, world] = [
    refs.viewport.current,
    refs.camera.current,
    refs.world.current,
  ];
  return viewport && camera && world ? { viewport, camera, world } : null;
}

function nextFlight(parts: CameraParts, shot: Shot, aim: Aim & { frame: Frame }) {
  if (!shot.frame) {
    return intro(parts, aim.frame);
  }
  if (shot.key === aim.key) {
    // Same shot after a resize or a font swap: settle at once rather than fly anywhere.
    place(parts, aim.frame);
    return null;
  }
  return fly(parts, shot.frame, aim.frame);
}

/** Flies the camera to each frame as the reader moves; without motion the page is a plain scroll. */
export function useCamera(refs: CameraRefs, aim: Aim, isCanvas: boolean): void {
  const shot = useRef<Shot>({ frame: null, key: null, flight: null });

  useGSAP(
    () => {
      const parts = partsOf(refs);
      if (!parts) {
        return;
      }
      if (!isCanvas || !aim.frame) {
        shot.current.flight?.kill();
        shot.current = { frame: null, key: null, flight: null };
        release(parts);
        return;
      }
      const isSameShot = shot.current.key === aim.key;
      if (!isSameShot || !shot.current.flight?.isActive()) {
        if (!isSameShot) {
          shot.current.flight?.kill();
        }
        const flight = nextFlight(parts, shot.current, { frame: aim.frame, key: aim.key });
        shot.current = { frame: aim.frame, key: aim.key, flight: flight ?? shot.current.flight };
      }
    },
    { dependencies: [aim.frame, aim.key, isCanvas] },
  );
}
