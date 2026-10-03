import { eventsHappenedBy, type Timeline } from "./timeline.ts";

const MILLISECONDS_PER_SECOND = 1000;
const KEY_STEP_MS = 5 * MILLISECONDS_PER_SECOND;
const KEY_PAGE_MS = 30 * MILLISECONDS_PER_SECOND;

export function clampPosition(positionMs: number, durationMs: number): number {
  return Math.min(Math.max(0, positionMs), Math.max(0, durationMs));
}

/**
 * The latest point at or before this position where the screen changed: the last event, or the
 * last whole second the clock shows, whichever is later. Between two such points neither the
 * X-ray nor the clock changes, so the page renders once per change rather than once per frame.
 */
export function settledPosition(timeline: Timeline, positionMs: number): number {
  const position = Math.max(0, positionMs);
  const lastEventMs = timeline.events[eventsHappenedBy(timeline, position) - 1]?.atMs ?? 0;
  const wholeSecondMs = Math.floor(position / MILLISECONDS_PER_SECOND) * MILLISECONDS_PER_SECOND;
  return Math.max(lastEventMs, wholeSecondMs);
}

/** Where a key pressed on the position slider moves the call to, or null for any other key. */
export function keyedPosition(key: string, positionMs: number, durationMs: number): number | null {
  const targets: Partial<Record<string, number>> = {
    ArrowLeft: positionMs - KEY_STEP_MS,
    ArrowDown: positionMs - KEY_STEP_MS,
    ArrowRight: positionMs + KEY_STEP_MS,
    ArrowUp: positionMs + KEY_STEP_MS,
    PageDown: positionMs - KEY_PAGE_MS,
    PageUp: positionMs + KEY_PAGE_MS,
    Home: 0,
    End: durationMs,
  };
  const target = targets[key];
  return target === undefined ? null : clampPosition(target, durationMs);
}

/** The point in the call under a pointer at `clientX` on a track spanning the whole call. */
export function positionAtPointer(
  clientX: number,
  track: Pick<DOMRect, "left" | "width">,
  durationMs: number,
): number {
  if (track.width <= 0) {
    return 0;
  }
  return clampPosition(((clientX - track.left) / track.width) * durationMs, durationMs);
}
