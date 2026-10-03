import { describe, expect, it } from "vitest";
import type { Recording } from "../call/demoReplay.ts";
import {
  LINE_LEAD_IN_MS,
  eventsHappenedBy,
  lineCueMs,
  toTimeline,
  viewAt,
  type Timeline,
} from "./timeline.ts";

const AT = "2026-10-03T15:00:00+09:00";

function transcript(lineId: string, ja: string, isFinal: boolean) {
  return {
    type: "transcript",
    line_id: lineId,
    speaker: lineId.startsWith("kenji") ? "kenji" : "caller",
    ja,
    is_final: isFinal,
    is_backchannel: false,
    at: AT,
  };
}

const recording: Recording = {
  source: "test",
  recorded_on: "2026-10-03",
  events: [
    {
      offset_ms: 0,
      event: { type: "call_started", call_id: "c1", transport: "browser", started_at: AT },
    },
    { offset_ms: 1000, event: transcript("kenji-1", "お電話ありがとうございます。", false) },
    { offset_ms: 4000, event: transcript("kenji-1", "お電話ありがとうございます。", true) },
    { offset_ms: 2500, event: { type: "flow_node", node: "greeting" } },
    { offset_ms: 4500, event: { type: "not-an-event" } },
    { offset_ms: 6000, event: transcript("caller-2", "佐藤", false) },
    { offset_ms: 7000, event: transcript("caller-2", "佐藤です。", true) },
    { offset_ms: 9000, event: { type: "call_ended", outcome: "no_agreement", ended_at: AT } },
  ],
};

const timeline: Timeline = toTimeline(recording);

describe("toTimeline", () => {
  it("keeps the valid events, oldest first, and ends at the last one", () => {
    expect(timeline.events.map(({ atMs }) => atMs)).toEqual([
      0, 1000, 2500, 4000, 6000, 7000, 9000,
    ]);
    expect(timeline.durationMs).toBe(9000);
  });

  it("leaves out an event with no usable offset", () => {
    const broken = toTimeline({
      ...recording,
      events: [{ offset_ms: Number.NaN, event: { type: "flow_node", node: "greeting" } }],
    });

    expect(broken).toEqual({ events: [], durationMs: 0 });
  });
});

describe("eventsHappenedBy", () => {
  it("counts the events at or before the position", () => {
    expect(eventsHappenedBy(timeline, 0)).toBe(1);
    expect(eventsHappenedBy(timeline, 3999)).toBe(3);
    expect(eventsHappenedBy(timeline, 4000)).toBe(4);
    expect(eventsHappenedBy(timeline, 60_000)).toBe(7);
  });
});

describe("viewAt", () => {
  it("shows a line Kenji is still saying, before it is final", () => {
    const view = viewAt(timeline, 2000);

    expect(view.status).toBe("live");
    expect(view.speaking?.lineId).toBe("kenji-1");
    expect(view.lines).toEqual([]);
  });

  it("shows only what had been said by that moment", () => {
    const view = viewAt(timeline, 6500);

    expect(view.lines.map(({ lineId }) => lineId)).toEqual(["kenji-1"]);
    expect(view.partial?.ja).toBe("佐藤");
    expect(view.node).toBe("greeting");
  });

  it("ends the call once the last event has happened", () => {
    const view = viewAt(timeline, 9000);

    expect(view.status).toBe("ended");
    expect(view.lines.map(({ lineId }) => lineId)).toEqual(["kenji-1", "caller-2"]);
  });

  it("goes back as readily as forward", () => {
    const later = viewAt(timeline, 7000);
    const earlier = viewAt(timeline, 500);

    expect(later.lines).toHaveLength(2);
    expect(earlier.lines).toEqual([]);
    expect(earlier.status).toBe("live");
  });
});

describe("lineCueMs", () => {
  it("cues a line just before its first word was transcribed", () => {
    expect(lineCueMs(timeline, "caller-2")).toBe(6000 - LINE_LEAD_IN_MS);
  });

  it("never cues before the call started", () => {
    expect(lineCueMs(timeline, "kenji-1")).toBe(Math.max(0, 1000 - LINE_LEAD_IN_MS));
  });

  it("has no cue for a line the call never had", () => {
    expect(lineCueMs(timeline, "kenji-99")).toBeNull();
  });
});
