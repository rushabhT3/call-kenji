import { describe, expect, it } from "vitest";
import type { CallerToneHeard, ComplianceUpdated, TurnEndJudged } from "../contract/events.ts";
import {
  LINE_UNREACHABLE,
  callerSounds,
  complianceSummary,
  microphoneProblem,
  nodeLabel,
  nowSentence,
  outcomeLabel,
  toneBadge,
  transcriptSummary,
  turnEndSentence,
} from "./copy.ts";

const compliance = (overrides: Partial<ComplianceUpdated> = {}): ComplianceUpdated => ({
  type: "compliance",
  calling_hours: "pass",
  identity_gate: "pass",
  offer_within_terms: "pending",
  ai_disclosure: "pass",
  recording_notice: "pass",
  ...overrides,
});

describe("nowSentence", () => {
  it("explains each step in one plain sentence", () => {
    expect(nowSentence("live", "verify_identity").en).toContain("who you play");
    expect(nowSentence("waiting", null).en).toBe("Waiting for your call.");
    expect(nowSentence("ended", "close").en).toContain("ended");
  });

  it("falls back to the node label for steps without a sentence", () => {
    expect(nowSentence("live", "human_handoff").en).toBe("Handing over to a person.");
  });
});

describe("labels", () => {
  it("names unknown nodes by their id rather than hiding them", () => {
    expect(nodeLabel("mystery").en).toBe("mystery");
  });

  it("states outcomes plainly", () => {
    expect(outcomeLabel("promise_to_pay").en).toBe("Payment plan agreed");
  });
});

describe("complianceSummary", () => {
  it("counts the safeguards holding", () => {
    expect(complianceSummary(compliance())).toBe("4 of 5 safeguards holding.");
  });

  it("says when a guardrail fired", () => {
    expect(complianceSummary(compliance({ offer_within_terms: "blocked" }))).toBe(
      "4 of 5 safeguards holding. 1 guardrail stopped something.",
    );
  });

  it("waits before the call starts", () => {
    expect(complianceSummary(null)).toBe("Waiting for the call to start.");
  });

  it("counts only the safeguards, not the note on calling hours", () => {
    const noted = compliance({ calling_hours_note: "03:12 in Tokyo." });

    expect(complianceSummary(noted)).toBe("4 of 5 safeguards holding.");
  });
});

describe("turnEndSentence", () => {
  const turnEnd = (overrides: Partial<TurnEndJudged> = {}): TurnEndJudged => ({
    type: "turn_end",
    finished_probability: 0.91,
    waited_for: "none",
    waited_ms: 30,
    ...overrides,
  });

  it("says Kenji answered when Smart Turn heard the end", () => {
    expect(turnEndSentence(turnEnd())).toBe(
      "Smart Turn: 91% sure you had finished, so Kenji answered.",
    );
  });

  it("says how long Kenji waited when Smart Turn heard you still talking", () => {
    const stillTalking = turnEnd({
      finished_probability: 0.23,
      waited_for: "still_talking",
      waited_ms: 1500,
    });

    expect(turnEndSentence(stillTalking)).toBe(
      "Smart Turn: 23% sure you had finished. You were still talking, so Kenji waited 1.50 s.",
    );
  });

  it("names the particle rule and the Hold button as reasons to wait", () => {
    const particle = turnEnd({
      finished_probability: null,
      waited_for: "unfinished_phrase",
      waited_ms: 2000,
    });
    const onHold = turnEnd({
      finished_probability: null,
      waited_for: "caller_hold",
      waited_ms: 8300,
    });

    expect(turnEndSentence(particle)).toBe(
      "Your words stopped mid-phrase, on a particle, so Kenji waited 2.00 s for the rest.",
    );
    expect(turnEndSentence(onHold)).toBe(
      "You pressed Hold, so Kenji waited 8.30 s, until you pressed Done.",
    );
  });

  it("falls back to the speech service when Smart Turn had no reading", () => {
    expect(turnEndSentence(turnEnd({ finished_probability: null }))).toBe(
      "Kenji answered as soon as the speech service heard you finish.",
    );
  });
});

describe("call problems", () => {
  it("tells a caller with a blocked microphone how to fix it", () => {
    expect(microphoneProblem("blocked")).toContain("Allow the microphone");
  });

  it("says what to do for every kind of microphone problem", () => {
    const reasons = [
      "blocked",
      "already-in-use",
      "not-found",
      "invalid-constraints",
      "not-supported",
      "unknown",
    ] as const;

    expect(reasons.every((reason) => microphoneProblem(reason).length > 0)).toBe(true);
  });

  it("never shows a technical error when the line cannot be reached", () => {
    expect(LINE_UNREACHABLE).not.toMatch(/ICE|offer|\[object/);
  });
});

describe("transcriptSummary", () => {
  it("counts the lines once the call is over", () => {
    expect(transcriptSummary("ended", 13)).toBe(
      "The whole call: 13 lines, Japanese with English underneath.",
    );
    expect(transcriptSummary("ended", 1)).toContain("1 line,");
  });
});

describe("how the caller sounds", () => {
  const tone = (
    emotion: CallerToneHeard["emotion"],
    sounds: CallerToneHeard["sounds"] = [],
  ): CallerToneHeard => ({ type: "caller_tone", line_id: "caller-2", emotion, sounds });

  it("badges a line with what stands out in the caller's voice", () => {
    expect(toneBadge(tone("angry"))).toBe("Sounds frustrated");
    expect(toneBadge(tone("sad", ["crying"]))).toBe("Sounds upset · cries");
    expect(toneBadge(tone("unknown", ["laughter"]))).toBe("Laughs");
  });

  it("leaves a calm or unclear line without a badge", () => {
    expect(toneBadge(tone("neutral"))).toBeNull();
    expect(toneBadge(tone("unknown"))).toBeNull();
  });

  it("tells the strategist card how the caller sounded, calm included", () => {
    expect(callerSounds(tone("neutral"))).toBe("Calm");
    expect(callerSounds(tone("angry", ["laughter"]))).toBe("Frustrated · laughs");
    expect(callerSounds(tone("unknown"))).toBe("Hard to tell");
  });
});
