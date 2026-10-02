import { describe, expect, it } from "vitest";
import type { CallEvent } from "../contract/events.ts";
import {
  EMPTY_CALL,
  applyEvents,
  elapsedMs,
  finishedCallMs,
  latestKenjiLineId,
} from "./callView.ts";

const START = "2026-10-02T15:00:00+09:00";

const transcript = (lineId: string, speaker: "caller" | "kenji", ja: string, isFinal = true) =>
  ({
    type: "transcript",
    line_id: lineId,
    speaker,
    ja,
    is_final: isFinal,
    is_backchannel: false,
    at: START,
  }) satisfies CallEvent;

describe("applyEvents", () => {
  it("starts a call and records the transport", () => {
    const view = applyEvents(EMPTY_CALL, [
      { type: "call_started", call_id: "c1", transport: "phone", started_at: START },
    ]);

    expect(view.status).toBe("live");
    expect(view.transport).toBe("phone");
  });

  it("replaces a partial caller line when its final arrives", () => {
    const view = applyEvents(EMPTY_CALL, [
      transcript("caller-1", "caller", "佐藤", false),
      transcript("caller-1", "caller", "佐藤ゆうきです。"),
    ]);

    expect(view.partial).toBeNull();
    expect(view.lines.map((line) => line.ja)).toEqual(["佐藤ゆうきです。"]);
  });

  it("keeps a subtitle that arrives before its line", () => {
    const view = applyEvents(EMPTY_CALL, [
      { type: "subtitle", line_id: "kenji-2", en: "Thank you." },
      transcript("kenji-2", "kenji", "ありがとうございます。"),
    ]);

    expect(view.subtitles["kenji-2"]).toBe("Thank you.");
  });

  it("collects every latency measurement in order", () => {
    const latency = (turn: number): CallEvent => ({
      type: "latency",
      turn,
      end_of_turn_ms: 300,
      llm_first_token_ms: 600,
      tts_first_audio_ms: 200,
      total_ms: 1100,
      p50_ms: 1100,
      p95_ms: 1100,
      budget_ms: 1500,
    });

    const view = applyEvents(EMPTY_CALL, [latency(1), latency(2)]);

    expect(view.latency.map((entry) => entry.turn)).toEqual([1, 2]);
  });

  it("ends the call with its outcome and clears speech in progress", () => {
    const view = applyEvents(EMPTY_CALL, [
      transcript("caller-3", "caller", "は", false),
      { type: "call_ended", outcome: "promise_to_pay", ended_at: START },
    ]);

    expect(view.status).toBe("ended");
    expect(view.outcome).toBe("promise_to_pay");
    expect(view.partial).toBeNull();
  });
});

describe("selectors", () => {
  it("finds Kenji's latest line", () => {
    const view = applyEvents(EMPTY_CALL, [
      transcript("kenji-1", "kenji", "一"),
      transcript("caller-2", "caller", "二"),
      transcript("kenji-3", "kenji", "三"),
    ]);

    expect(latestKenjiLineId(view)).toBe("kenji-3");
  });

  it("measures elapsed time and never goes negative", () => {
    expect(elapsedMs(START, "2026-10-02T15:02:14+09:00")).toBe(134_000);
    expect(elapsedMs("2026-10-02T15:02:14+09:00", START)).toBe(0);
  });

  it("times a finished call by its own clock, however fast it was replayed", () => {
    const started = applyEvents(EMPTY_CALL, [
      { type: "call_started", call_id: "c1", transport: "browser", started_at: START },
    ]);
    const ended = applyEvents(started, [
      { type: "call_ended", outcome: "promise_to_pay", ended_at: "2026-10-02T15:02:20+09:00" },
    ]);

    expect(finishedCallMs(started)).toBeNull();
    expect(finishedCallMs(ended)).toBe(140_000);
  });
});
