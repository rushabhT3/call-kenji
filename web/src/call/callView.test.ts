import { describe, expect, it } from "vitest";
import type { CallEvent } from "../contract/events.ts";
import {
  EMPTY_CALL,
  applyEvents,
  currentKenjiLineId,
  elapsedMs,
  finishedCallMs,
  latestCallerTone,
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

  it("records the persona the caller plays, when the server says", () => {
    const started = {
      type: "call_started",
      call_id: "c1",
      transport: "browser",
      started_at: START,
    } satisfies CallEvent;

    const named = applyEvents(EMPTY_CALL, [{ ...started, persona_id: "tanaka" }]);
    const unnamed = applyEvents(EMPTY_CALL, [started]);

    expect(named.personaId).toBe("tanaka");
    expect(unnamed.personaId).toBeNull();
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

describe("Kenji's line in progress", () => {
  it("shows the line he is saying and replaces it when he finishes", () => {
    const speaking = applyEvents(EMPTY_CALL, [transcript("kenji-3", "kenji", "ご確認", false)]);
    const finished = applyEvents(speaking, [
      transcript("kenji-3", "kenji", "ご確認ありがとうございます。"),
    ]);

    expect(speaking.speaking?.ja).toBe("ご確認");
    expect(finished.speaking).toBeNull();
    expect(finished.lines.map((line) => line.ja)).toEqual(["ご確認ありがとうございます。"]);
  });

  it("keeps the caller's words in progress apart from Kenji's", () => {
    const view = applyEvents(EMPTY_CALL, [
      transcript("kenji-3", "kenji", "ご確認", false),
      transcript("caller-4", "caller", "はい", false),
    ]);

    expect(view.speaking?.lineId).toBe("kenji-3");
    expect(view.partial?.lineId).toBe("caller-4");
  });

  it("is the current line while he says it", () => {
    const view = applyEvents(EMPTY_CALL, [
      transcript("kenji-1", "kenji", "お電話ありがとうございます。"),
      transcript("kenji-3", "kenji", "ご確認", false),
    ]);

    expect(currentKenjiLineId(view)).toBe("kenji-3");
  });
});

describe("subtitles", () => {
  it("records a translation that failed for good as missing", () => {
    const view = applyEvents(EMPTY_CALL, [
      { type: "subtitle", line_id: "kenji-2", en: "", is_unavailable: true },
    ]);

    expect(view.subtitles["kenji-2"]).toBeNull();
  });
});

describe("how the caller sounds", () => {
  const tone = (lineId: string, emotion: "angry" | "neutral") =>
    ({ type: "caller_tone", line_id: lineId, emotion, sounds: [] }) satisfies CallEvent;

  it("keeps each tone with the caller's line it was heard on", () => {
    const view = applyEvents(EMPTY_CALL, [
      transcript("caller-2", "caller", "今月は少し厳しいです。"),
      tone("caller-2", "angry"),
    ]);

    expect(view.tones["caller-2"]?.emotion).toBe("angry");
  });

  it("gives the tone of the latest caller line that was heard", () => {
    const view = applyEvents(EMPTY_CALL, [
      transcript("caller-2", "caller", "今月は少し厳しいです。"),
      tone("caller-2", "angry"),
      transcript("caller-4", "caller", "来月なら払えます。"),
      tone("caller-4", "neutral"),
      transcript("caller-6", "caller", "はい。"),
    ]);

    expect(latestCallerTone(view)?.line_id).toBe("caller-4");
  });

  it("has no tone before a caller line is heard", () => {
    const view = applyEvents(EMPTY_CALL, [transcript("caller-2", "caller", "はい。")]);

    expect(latestCallerTone(view)).toBeNull();
  });
});
