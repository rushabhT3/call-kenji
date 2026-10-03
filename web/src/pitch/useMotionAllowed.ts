import { useSyncExternalStore } from "react";

const MOTION_OK = "(prefers-reduced-motion: no-preference)";

function subscribe(onChange: () => void): () => void {
  const query = window.matchMedia(MOTION_OK);
  query.addEventListener("change", onChange);
  return () => {
    query.removeEventListener("change", onChange);
  };
}

function isMotionAllowed(): boolean {
  return window.matchMedia(MOTION_OK).matches;
}

/** False for readers who asked for less motion: they get the pitch as a page to scroll. */
export function useMotionAllowed(): boolean {
  return useSyncExternalStore(subscribe, isMotionAllowed, () => false);
}
