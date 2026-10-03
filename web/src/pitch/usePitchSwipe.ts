import { useRef, type PointerEvent } from "react";

/** A swipe shorter than this is a tap or a wobble, not a request to move on. */
const SWIPE_DISTANCE = 60;

export interface SwipeHandlers {
  onPointerDown: (event: PointerEvent) => void;
  onPointerUp: (event: PointerEvent) => void;
}

/** Swiping left moves on and swiping right goes back, as in a phone's photo viewer. */
export function usePitchSwipe(next: () => void, previous: () => void): SwipeHandlers {
  const start = useRef<{ x: number; y: number } | null>(null);
  return {
    onPointerDown: (event) => {
      // A mouse drag is usually someone selecting text; swipes come from fingers and pens.
      start.current = event.pointerType === "mouse" ? null : { x: event.clientX, y: event.clientY };
    },
    onPointerUp: (event) => {
      const from = start.current;
      start.current = null;
      if (!from) {
        return;
      }
      const across = event.clientX - from.x;
      const down = event.clientY - from.y;
      if (Math.abs(across) >= SWIPE_DISTANCE && Math.abs(across) > Math.abs(down)) {
        if (across < 0) {
          next();
        } else {
          previous();
        }
      }
    },
  };
}
