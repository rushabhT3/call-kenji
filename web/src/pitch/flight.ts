import { gsap } from "gsap";
import { cameraFor, travelScale, type Frame, type Size } from "./camera.ts";

export interface CameraParts {
  viewport: HTMLElement;
  camera: HTMLElement;
  world: HTMLElement;
}

const SHORTEST_FLIGHT = 0.9;
const LONGEST_FLIGHT = 2;
/** Seconds of flight per world pixel travelled, so a hop across the map takes longer than a nudge. */
const SECONDS_PER_PIXEL = 0.00025;
/** Share of the flight spent pulling back before diving in again. */
const PULL_BACK_SHARE = 0.45;
/** A pull-back this close to the current zoom is not worth the dip. */
const PULL_BACK_THRESHOLD = 0.9;
const INTRO_START_SCALE = 0.82;
const INTRO_SECONDS = 1.4;

export function sizeOf(element: HTMLElement): Size {
  return { width: element.clientWidth, height: element.clientHeight };
}

function flightSeconds(from: Frame, to: Frame): number {
  const distance = Math.hypot(to.cx - from.cx, to.cy - from.cy);
  return Math.min(
    Math.max(SHORTEST_FLIGHT + distance * SECONDS_PER_PIXEL, SHORTEST_FLIGHT),
    LONGEST_FLIGHT,
  );
}

/** Puts the camera on a frame at once: on load, on resize, and for every cut without motion. */
export function place(parts: CameraParts, frame: Frame): void {
  const target = cameraFor(sizeOf(parts.viewport), frame);
  gsap.set(parts.world, { x: target.x, y: target.y });
  gsap.set(parts.camera, { scale: target.scale, rotation: target.rotation, autoAlpha: 1 });
}

/** The opening shot: the whole universe settles into view. */
export function intro(parts: CameraParts, frame: Frame): gsap.core.Tween {
  const target = cameraFor(sizeOf(parts.viewport), frame);
  gsap.set(parts.world, { x: target.x, y: target.y });
  return gsap.fromTo(
    parts.camera,
    { scale: target.scale * INTRO_START_SCALE, rotation: target.rotation, autoAlpha: 0 },
    { scale: target.scale, autoAlpha: 1, duration: INTRO_SECONDS, ease: "power3.out" },
  );
}

/** Prezi's move: pull back far enough to see where you are going, travel, then dive in. */
export function fly(parts: CameraParts, from: Frame, to: Frame): gsap.core.Timeline {
  const viewport = sizeOf(parts.viewport);
  const target = cameraFor(viewport, to);
  const seconds = flightSeconds(from, to);
  const nowScale = Number(gsap.getProperty(parts.camera, "scale"));
  const pullBack = travelScale(viewport, from, to);
  const timeline = gsap.timeline();
  timeline.to(
    parts.world,
    { x: target.x, y: target.y, duration: seconds, ease: "power3.inOut" },
    0,
  );
  if (pullBack < Math.min(nowScale, target.scale) * PULL_BACK_THRESHOLD) {
    const dip = seconds * PULL_BACK_SHARE;
    timeline
      .to(parts.camera, { scale: pullBack, rotation: 0, duration: dip, ease: "power2.inOut" }, 0)
      .to(
        parts.camera,
        {
          scale: target.scale,
          rotation: target.rotation,
          duration: seconds - dip,
          ease: "power2.inOut",
        },
        dip,
      );
  } else {
    timeline.to(
      parts.camera,
      { scale: target.scale, rotation: target.rotation, duration: seconds, ease: "power2.inOut" },
      0,
    );
  }
  return timeline;
}

/** Hands the page back to the stylesheet when motion is turned off. */
export function release(parts: CameraParts): void {
  // Only what GSAP set: the world's inline style also carries the layout's custom properties.
  gsap.set([parts.camera, parts.world], { clearProps: "transform,opacity,visibility" });
}
