import { EMPTY_CALL, applyEvents, type CallView } from "../call/callView.ts";
import type { Recording } from "../call/demoReplay.ts";
import { parseCallEvent, type CallEvent } from "../contract/events.ts";

/** One event of a recorded call, at its offset from the moment the call started. */
export interface TimedEvent {
  atMs: number;
  event: CallEvent;
}

/** A recorded call's events in the order they happened, and when the last one happened. */
export interface Timeline {
  events: readonly TimedEvent[];
  durationMs: number;
}

/**
 * A line is cued this long before its first word was transcribed: speech recognition hears a
 * word only after it has begun, so cueing at the transcript would clip the word.
 */
export const LINE_LEAD_IN_MS = 500;

function isOffset(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value) && value >= 0;
}

/** The recording's valid events, oldest first; anything unreadable is left out. */
export function toTimeline(recording: Recording): Timeline {
  const events = recording.events
    .flatMap(({ offset_ms, event }): TimedEvent[] => {
      const parsed = parseCallEvent(event);
      return parsed && isOffset(offset_ms) ? [{ atMs: offset_ms, event: parsed }] : [];
    })
    .toSorted((first, second) => first.atMs - second.atMs);
  return { events, durationMs: events.at(-1)?.atMs ?? 0 };
}

/** How many of the call's events have happened by this point in it. */
export function eventsHappenedBy(timeline: Timeline, positionMs: number): number {
  return timeline.events.findLastIndex(({ atMs }) => atMs <= positionMs) + 1;
}

/** The X-ray once the call's first `count` events have happened. */
export function viewAfter(timeline: Timeline, count: number): CallView {
  return applyEvents(
    EMPTY_CALL,
    timeline.events.slice(0, count).map(({ event }) => event),
  );
}

/** The X-ray as it stood at this point in the call. */
export function viewAt(timeline: Timeline, positionMs: number): CallView {
  return viewAfter(timeline, eventsHappenedBy(timeline, positionMs));
}

/** Where to play a line from, or null when the call has no such line. */
export function lineCueMs(timeline: Timeline, lineId: string): number | null {
  const first = timeline.events.find(
    ({ event }) => event.type === "transcript" && event.line_id === lineId,
  );
  return first ? Math.max(0, first.atMs - LINE_LEAD_IN_MS) : null;
}
