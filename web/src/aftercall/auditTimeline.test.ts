import { describe, expect, it } from "vitest";
import type { AuditPublished } from "../contract/events.ts";
import { auditTimeline } from "./auditTimeline.ts";

const record = (sequence: number, kind: string, payload: object, second: number) => ({
  sequence,
  kind,
  recorded_at: `2026-10-03T15:00:${String(second).padStart(2, "0")}+09:00`,
  payload,
});

const audit = (records: Record<string, unknown>[]): AuditPublished => ({
  type: "audit",
  is_chain_valid: true,
  head_hash: "0".repeat(64),
  records,
});

describe("auditTimeline", () => {
  it("times each entry from the first record", () => {
    const entries = auditTimeline(
      audit([
        record(0, "node_entered", { node: "greeting" }, 0),
        record(1, "disclosure_given", {}, 22),
      ]),
    );

    expect(entries.map((entry) => entry.offsetMs)).toEqual([0, 22_000]);
  });

  it("explains a rejected offer by the terms it breaks", () => {
    const [entry] = auditTimeline(
      audit([
        record(
          0,
          "terms_checked",
          {
            monthly_yen: 3000,
            installments: 12,
            first_payment_on: "2026-10-17",
            accepted: false,
            violations: ["below_minimum_monthly", "too_many_installments"],
          },
          0,
        ),
      ]),
    );

    expect(entry?.tone).toBe("warn");
    expect(entry?.detail).toBe(
      "¥3,000 a month, 12 payments from 17 Oct: the monthly amount is below the minimum; it would take too many payments",
    );
  });

  it("marks what the call decided", () => {
    const [entry] = auditTimeline(
      audit([record(0, "outcome_decided", { outcome: "promise_to_pay" }, 0)]),
    );

    expect(entry).toMatchObject({ title: "Outcome: Payment plan agreed", tone: "key" });
  });

  it("names a kind it does not know rather than hiding it", () => {
    const [entry] = auditTimeline(audit([record(0, "something_new", {}, 0)]));

    expect(entry?.title).toBe("Something new");
  });
});
