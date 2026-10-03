import { describe, expect, it } from "vitest";
import recording from "../../public/demo/call.json";
import { parseCallEvent, parseViewerReady } from "./events.ts";

describe("parseCallEvent", () => {
  it("accepts every event the server recorded for the demo", () => {
    const rejected = recording.events.filter(({ event }) => parseCallEvent(event) === null);

    expect(rejected).toEqual([]);
  });

  it("accepts how the caller sounded on a line, and needs its sounds", () => {
    const tone = { type: "caller_tone", line_id: "caller-3", emotion: "angry", sounds: [] };

    expect(parseCallEvent(tone)).toEqual(tone);
    expect(parseCallEvent({ ...tone, sounds: "laughter" })).toBeNull();
  });

  it("accepts a compliance update recorded before the calling-hours note", () => {
    const compliance = {
      type: "compliance",
      calling_hours: "pass",
      identity_gate: "pending",
      offer_within_terms: "pending",
      ai_disclosure: "pass",
      recording_notice: "pass",
    };

    expect(parseCallEvent(compliance)).toEqual(compliance);
  });

  it("accepts a turn end that Smart Turn had no reading for", () => {
    const turnEnd = {
      type: "turn_end",
      finished_probability: null,
      waited_for: "none",
      waited_ms: 0.4,
    };

    expect(parseCallEvent(turnEnd)).toEqual(turnEnd);
    expect(parseCallEvent({ type: "turn_end", waited_for: "none" })).toBeNull();
  });

  it("rejects unknown types and incomplete events", () => {
    expect(parseCallEvent({ type: "mystery" })).toBeNull();
    expect(parseCallEvent({ type: "flow_node" })).toBeNull();
    expect(parseCallEvent("flow_node")).toBeNull();
  });
});

describe("parseViewerReady", () => {
  it("reads the code the server issues to this tab", () => {
    expect(parseViewerReady({ type: "viewer_ready", viewer_id: "v", code: "4812" })).toEqual({
      type: "viewer_ready",
      viewer_id: "v",
      code: "4812",
    });
    expect(parseViewerReady({ type: "viewer_ready", code: 4812 })).toBeNull();
  });
});
