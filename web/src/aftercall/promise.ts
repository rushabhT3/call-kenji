import type { AuditPublished } from "../contract/events.ts";

export interface PromiseFacts {
  monthlyYen: number;
  installments: number;
  firstPaymentOn: string;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

/** The agreed plan, read from the audit record rather than trusted from anywhere else. */
export function promiseFromAudit(audit: AuditPublished | null): PromiseFacts | null {
  const record = audit?.records.findLast((entry) => entry.kind === "promise_recorded");
  const payload = record?.payload;
  if (!isRecord(payload)) {
    return null;
  }
  const { monthly_yen: monthlyYen, installments, first_payment_on: firstPaymentOn } = payload;
  if (
    typeof monthlyYen !== "number" ||
    typeof installments !== "number" ||
    typeof firstPaymentOn !== "string"
  ) {
    return null;
  }
  return { monthlyYen, installments, firstPaymentOn };
}
