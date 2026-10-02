import { describe, expect, it } from "vitest";
import recording from "../../public/demo/call.json";
import { parseCallEvent, parseViewerReady } from "./events.ts";

describe("parseCallEvent", () => {
  it("accepts every event the server recorded for the demo", () => {
    const rejected = recording.events.filter(({ event }) => parseCallEvent(event) === null);

    expect(rejected).toEqual([]);
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
