import type { Speaker } from "../contract/events.ts";
import type { Timeline } from "./timeline.ts";

/** A stretch of the recording in which one side of the call is speaking one line. */
export interface SpeakerRegion {
  lineId: string;
  speaker: Speaker;
  startMs: number;
  endMs: number;
}

interface LineSpan {
  lineId: string;
  speaker: Speaker;
  startMs: number;
  finalMs: number | null;
}

/** Each line's first transcript event and its final one, in the order the lines began. */
function lineSpans(timeline: Timeline): LineSpan[] {
  const spans = new Map<string, LineSpan>();
  for (const { atMs, event } of timeline.events) {
    if (event.type === "transcript") {
      const span = spans.get(event.line_id) ?? {
        lineId: event.line_id,
        speaker: event.speaker,
        startMs: atMs,
        finalMs: null,
      };
      const isFirstFinal = event.is_final && span.finalMs === null;
      spans.set(event.line_id, isFirstFinal ? { ...span, finalMs: atMs } : span);
    }
  }
  return [...spans.values()];
}

/**
 * Who is speaking when. A line starts at its first transcript event: when Kenji starts saying
 * it, or at the caller's first recognised word. It ends at its final event: when Kenji has said
 * it, or when the caller's words settle. A line the recording never settles lasts until the
 * next line starts, or to the end of the call.
 */
export function speakerRegions(timeline: Timeline): SpeakerRegion[] {
  const spans = lineSpans(timeline);
  return spans.map((span, index) => ({
    lineId: span.lineId,
    speaker: span.speaker,
    startMs: span.startMs,
    endMs: span.finalMs ?? spans[index + 1]?.startMs ?? timeline.durationMs,
  }));
}
