import { describe, expect, it } from "vitest";
import type { AuditPublished } from "../contract/events.ts";
import { promiseFromAudit } from "./promise.ts";

const audit = (records: Record<string, unknown>[]): AuditPublished => ({
  type: "audit",
  is_chain_valid: true,
  head_hash: "0".repeat(64),
  records,
});

describe("promiseFromAudit", () => {
  it("reads the recorded promise", () => {
    const facts = promiseFromAudit(
      audit([
        { kind: "terms_checked", payload: { monthly_yen: 3000 } },
        {
          kind: "promise_recorded",
          payload: { monthly_yen: 6000, installments: 6, first_payment_on: "2026-10-16" },
        },
      ]),
    );

    expect(facts).toEqual({ monthlyYen: 6000, installments: 6, firstPaymentOn: "2026-10-16" });
  });

  it("finds nothing when no promise was made", () => {
    expect(promiseFromAudit(audit([{ kind: "call_ended", payload: {} }]))).toBeNull();
    expect(promiseFromAudit(null)).toBeNull();
  });
});
