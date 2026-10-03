import { describe, expect, it } from "vitest";
import demoRecording from "../../public/demo/call.json";
import type { CallEvent } from "../contract/events.ts";
import { speakerRegions } from "./speakerRegions.ts";
import { toTimeline, type Timeline } from "./timeline.ts";

function line(lineId: string, isFinal: boolean, isBackchannel = false): CallEvent {
  return {
    type: "transcript",
    line_id: lineId,
    speaker: lineId.startsWith("kenji") ? "kenji" : "caller",
    ja: "はい",
    is_final: isFinal,
    is_backchannel: isBackchannel,
    at: "2026-10-03T15:00:00+09:00",
  };
}

function timelineOf(events: [number, CallEvent][], durationMs: number): Timeline {
  return { events: events.map(([atMs, event]) => ({ atMs, event })), durationMs };
}

describe("speakerRegions", () => {
  it("runs each line from its first transcript event to its final one", () => {
    const timeline = timelineOf(
      [
        [1000, line("kenji-1", false)],
        [5000, line("kenji-1", true)],
        [6000, line("caller-2", false)],
        [6400, line("caller-2", false)],
        [8000, line("caller-2", true)],
      ],
      9000,
    );

    expect(speakerRegions(timeline)).toEqual([
      { lineId: "kenji-1", speaker: "kenji", startMs: 1000, endMs: 5000 },
      { lineId: "caller-2", speaker: "caller", startMs: 6000, endMs: 8000 },
    ]);
  });

  it("ends a line that never settles where the next line starts", () => {
    const timeline = timelineOf(
      [
        [1000, line("kenji-1", false)],
        [3000, line("caller-2", false)],
        [4000, line("caller-2", true)],
      ],
      9000,
    );

    expect(speakerRegions(timeline)[0]).toMatchObject({ startMs: 1000, endMs: 3000 });
  });

  it("ends the last line that never settles at the end of the call", () => {
    const timeline = timelineOf([[7000, line("kenji-3", false)]], 9000);

    expect(speakerRegions(timeline)).toEqual([
      { lineId: "kenji-3", speaker: "kenji", startMs: 7000, endMs: 9000 },
    ]);
  });

  it("lets an aizuchi overlap the line Kenji is still saying", () => {
    const timeline = timelineOf(
      [
        [1000, line("kenji-1", false)],
        [2000, line("caller-2", false, true)],
        [2300, line("caller-2", true, true)],
        [5000, line("kenji-1", true)],
      ],
      9000,
    );

    expect(speakerRegions(timeline)).toEqual([
      { lineId: "kenji-1", speaker: "kenji", startMs: 1000, endMs: 5000 },
      { lineId: "caller-2", speaker: "caller", startMs: 2000, endMs: 2300 },
    ]);
  });

  it("keeps a line's first final event when the recording repeats it", () => {
    const timeline = timelineOf(
      [
        [1000, line("kenji-1", false)],
        [4000, line("kenji-1", true)],
        [4200, line("kenji-1", true)],
      ],
      9000,
    );

    expect(speakerRegions(timeline)[0]?.endMs).toBe(4000);
  });

  it("finds no one speaking in a call with no transcript", () => {
    expect(speakerRegions(timelineOf([], 0))).toEqual([]);
  });

  it("marks every line of the demo recording, each one heard for a while", () => {
    const regions = speakerRegions(toTimeline(demoRecording));

    expect(regions).toHaveLength(11);
    expect(regions.filter(({ speaker }) => speaker === "caller")).toHaveLength(4);
    expect(regions.every(({ startMs, endMs }) => endMs > startMs)).toBe(true);
  });
});
