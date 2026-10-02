import { elapsedMs } from "../call/callView.ts";
import { nodeLabel, outcomeText } from "../call/copy.ts";
import type { AuditPublished } from "../contract/events.ts";
import { formatCount, formatDay } from "../format.ts";

/** step: the call moved on; pass: a safeguard held; key: what the call decided; warn: refused. */
export type EntryTone = "step" | "pass" | "key" | "warn";

export interface TimelineEntry {
  sequence: number;
  offsetMs: number;
  title: string;
  detail: string | null;
  tone: EntryTone;
}

type Payload = Readonly<Record<string, unknown>>;
type Description = Omit<TimelineEntry, "sequence" | "offsetMs">;

const VIOLATIONS: Readonly<Record<string, string>> = {
  below_minimum_monthly: "the monthly amount is below the minimum",
  too_many_installments: "it would take too many payments",
  first_payment_in_past: "the first payment date has already passed",
  first_payment_too_late: "the first payment is more than 45 days away",
};

function isRecord(value: unknown): value is Payload {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function text(payload: Payload, key: string): string {
  const value = payload[key];
  return typeof value === "string" ? value : "";
}

function count(payload: Payload, key: string): number {
  const value = payload[key];
  return typeof value === "number" ? value : 0;
}

function plural(amount: number, noun: string): string {
  return `${String(amount)} ${noun}${amount === 1 ? "" : "s"}`;
}

function humanize(kind: string): string {
  const words = kind.replaceAll("_", " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

function plan(payload: Payload): string {
  const firstOn = text(payload, "first_payment_on");
  const from = firstOn ? ` from ${formatDay(firstOn)}` : "";
  const payments = plural(count(payload, "installments"), "payment");
  return `¥${formatCount(count(payload, "monthly_yen"))} a month, ${payments}${from}`;
}

function brokenTerms(payload: Payload): string {
  const violations = payload.violations;
  const reasons = Array.isArray(violations)
    ? violations.map((violation) => VIOLATIONS[String(violation)] ?? humanize(String(violation)))
    : [];
  return reasons.length > 0 ? `: ${reasons.join("; ")}` : "";
}

function identity(payload: Payload): Description {
  const failed = count(payload, "failed_attempts");
  const wrong = plural(failed, "wrong answer");
  switch (text(payload, "status")) {
    case "verified":
      return {
        title: "Identity confirmed",
        detail: failed > 0 ? `After ${wrong}.` : "On the first answer.",
        tone: "pass",
      };
    case "locked_out":
      return {
        title: "Identity check locked",
        detail: `${wrong}, so nothing about the account was shared.`,
        tone: "warn",
      };
    default:
      return {
        title: "Identity not confirmed yet",
        detail: failed > 0 ? `${wrong}.` : null,
        tone: "warn",
      };
  }
}

function terms(payload: Payload): Description {
  return payload.accepted === true
    ? { title: "Offer checked: inside the terms", detail: plan(payload), tone: "pass" }
    : {
        title: "Offer checked: outside the terms",
        detail: `${plan(payload)}${brokenTerms(payload)}`,
        tone: "warn",
      };
}

const DESCRIBERS: Readonly<Record<string, (payload: Payload) => Description>> = {
  node_entered: (payload) => ({
    title: `Moved on: ${nodeLabel(text(payload, "node")).en}`,
    detail: null,
    tone: "step",
  }),
  disclosure_given: () => ({
    title: "Said he is an AI and that this is a demo",
    detail: "Also said the call is kept as text and deleted after 30 days.",
    tone: "pass",
  }),
  identity_checked: identity,
  account_summary_requested: (payload) =>
    payload.locked === true
      ? { title: "Account details withheld", detail: "Identity was not confirmed.", tone: "warn" }
      : { title: "Account details opened for the confirmed caller", detail: null, tone: "step" },
  terms_checked: terms,
  promise_recorded: (payload) => ({
    title: "Payment promise recorded",
    detail: plan(payload),
    tone: "key",
  }),
  handoff_requested: (payload) => ({
    title: "Handover to a person requested",
    detail: text(payload, "summary") || text(payload, "reason") || null,
    tone: "key",
  }),
  stop_contact_recorded: () => ({
    title: "Request to stop contact recorded",
    detail: null,
    tone: "key",
  }),
  outcome_decided: (payload) => ({
    title: `Outcome: ${outcomeText(text(payload, "outcome"))}`,
    detail: null,
    tone: "key",
  }),
  call_ended: () => ({ title: "Call ended", detail: null, tone: "step" }),
  time_limit_reached: (payload) => ({
    title: "Time limit reached",
    detail: `${plural(Math.round(count(payload, "seconds") / 60), "minute")} is the most a call may last.`,
    tone: "warn",
  }),
  ended_without_agreement: (payload) => ({
    title: "Ended without an agreement",
    detail: text(payload, "reason") || null,
    tone: "step",
  }),
  call_refused: (payload) => ({
    title: "Call refused",
    detail: text(payload, "line") || null,
    tone: "warn",
  }),
};

function describe(kind: string, payload: Payload): Description {
  const describer = DESCRIBERS[kind];
  return describer ? describer(payload) : { title: humanize(kind), detail: null, tone: "step" };
}

/** The audit records in plain words, timed from the first record. */
export function auditTimeline(audit: AuditPublished): TimelineEntry[] {
  const firstAt = audit.records[0]?.recorded_at;
  return audit.records.map((record, index) => {
    const payload = isRecord(record.payload) ? record.payload : {};
    const at = typeof record.recorded_at === "string" ? record.recorded_at : null;
    return {
      sequence: typeof record.sequence === "number" ? record.sequence : index,
      offsetMs: typeof firstAt === "string" && at ? elapsedMs(firstAt, at) : 0,
      ...describe(String(record.kind), payload),
    };
  });
}
