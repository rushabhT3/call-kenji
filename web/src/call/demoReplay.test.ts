import { describe, expect, it } from "vitest";
import { isDemoMode, replaySchedule, replaySpeed, type Recording } from "./demoReplay.ts";

const recording: Recording = {
  source: "test",
  recorded_on: "2026-10-02",
  events: [
    { offset_ms: 0, event: { type: "flow_node", node: "greeting" } },
    { offset_ms: 2000, event: { type: "not-an-event" } },
    { offset_ms: 4000, event: { type: "flow_node", node: "verify_identity" } },
  ],
};

describe("replaySchedule", () => {
  it("keeps valid events and scales their timing", () => {
    const schedule = replaySchedule(recording, 2);

    expect(schedule.map(({ delayMs }) => delayMs)).toEqual([0, 2000]);
    expect(schedule.map(({ event }) => event.type)).toEqual(["flow_node", "flow_node"]);
  });

  it("refuses a speed that cannot play", () => {
    expect(() => replaySchedule(recording, 0)).toThrow("positive");
  });
});

describe("query options", () => {
  it("reads demo mode and speed from the query string", () => {
    expect(isDemoMode("?demo=1")).toBe(true);
    expect(isDemoMode("?demo=0")).toBe(false);
    expect(replaySpeed("?demo=1&speed=20")).toBe(20);
    expect(replaySpeed("?speed=-3")).toBe(1);
  });
});
