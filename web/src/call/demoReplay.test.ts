import { describe, expect, it } from "vitest";
import { isDemoMode, recordingAudioUrl, replaySpeed, type Recording } from "./demoReplay.ts";

const recording: Recording = {
  source: "test",
  recorded_on: "2026-10-02",
  events: [{ offset_ms: 0, event: { type: "flow_node", node: "greeting" } }],
};

describe("query options", () => {
  it("reads demo mode and speed from the query string", () => {
    expect(isDemoMode("?demo=1")).toBe(true);
    expect(isDemoMode("?demo=0")).toBe(false);
    expect(replaySpeed("?demo=1&speed=20")).toBe(20);
    expect(replaySpeed("?speed=-3")).toBe(1);
  });
});

describe("recordingAudioUrl", () => {
  it("finds the audio beside the recording, at normal speed only", () => {
    const withAudio = { ...recording, audio: "call.m4a" };

    expect(recordingAudioUrl(withAudio, 1, "/demo/call.json")).toBe("/demo/call.m4a");
    expect(recordingAudioUrl(withAudio, 4, "/demo/call.json")).toBeNull();
    expect(recordingAudioUrl(recording, 1, "/demo/call.json")).toBeNull();
  });
});
