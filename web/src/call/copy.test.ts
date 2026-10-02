import { describe, expect, it } from "vitest";
import type { ComplianceUpdated } from "../contract/events.ts";
import {
  LINE_UNREACHABLE,
  complianceSummary,
  microphoneProblem,
  nodeLabel,
  nowSentence,
  outcomeLabel,
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
    expect(nowSentence("live", "verify_identity").en).toContain("Yuki Sato");
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
