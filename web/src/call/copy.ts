import type { CallOutcome, CheckStatus, ComplianceUpdated } from "../contract/events.ts";
import type { CallStatus } from "./callView.ts";

export interface Bilingual {
  en: string;
  ja: string;
}

export const NODE_LABELS: Readonly<Record<string, Bilingual>> = {
  greeting: { en: "Introducing himself", ja: "ごあいさつ" },
  verify_identity: { en: "Checking identity", ja: "本人確認" },
  state_balance: { en: "Stating the balance", ja: "お支払い状況のご案内" },
  listen: { en: "Listening to your situation", ja: "ご事情の確認" },
  negotiate: { en: "Agreeing a plan", ja: "お支払い方法のご相談" },
  read_back: { en: "Reading the agreement back", ja: "お約束内容の読み上げ" },
  close: { en: "Closing the call", ja: "終話" },
  third_party: { en: "Asking for a callback", ja: "折り返しのお願い" },
  human_handoff: { en: "Handing over to a person", ja: "担当者への引き継ぎ" },
  stop_contact: { en: "Stopping further contact", ja: "連絡停止の記録" },
  identity_locked: { en: "Ending: identity not confirmed", ja: "本人確認不可" },
};

const NOW_SENTENCES: Readonly<Record<string, Bilingual>> = {
  greeting: {
    en: "Telling you he is an AI, that this is a demo, and how the call is recorded.",
    ja: "AIであること、デモであること、記録について説明しています。",
  },
  verify_identity: {
    en: "Checking that you are Yuki Sato before saying anything about the account.",
    ja: "口座の話をする前に、ご本人様かどうかを確認しています。",
  },
  state_balance: {
    en: "Identity confirmed. Telling you what is overdue.",
    ja: "本人確認が済み、未納の内容をお伝えしています。",
  },
  listen: {
    en: "Listening to your situation before suggesting anything.",
    ja: "提案の前に、ご事情を伺っています。",
  },
  negotiate: {
    en: "Working out a monthly amount that fits inside the terms.",
    ja: "条件の範囲内で、毎月のお支払い額を相談しています。",
  },
  read_back: {
    en: "Reading the agreement back so you can confirm it.",
    ja: "合意内容を読み上げ、確認をお願いしています。",
  },
};

const ENDINGS: Readonly<Record<CallOutcome, Bilingual>> = {
  promise_to_pay: { en: "Payment plan agreed", ja: "お支払いのお約束" },
  human_handoff: { en: "Handed over to a person", ja: "担当者へ引き継ぎ" },
  stop_contact: { en: "Further contact stopped", ja: "連絡停止" },
  callback_requested: { en: "Callback requested, nothing disclosed", ja: "折り返しのお願い" },
  identity_not_verified: { en: "Identity not confirmed", ja: "本人確認できず" },
  outside_calling_hours: { en: "Outside calling hours", ja: "受付時間外" },
  daily_limit_reached: { en: "Demo limit reached", ja: "本日の受付終了" },
  no_agreement: { en: "No agreement this time", ja: "今回は合意なし" },
};

export function outcomeLabel(outcome: CallOutcome): Bilingual {
  return ENDINGS[outcome];
}

export function nodeLabel(node: string): Bilingual {
  return NODE_LABELS[node] ?? { en: node, ja: node };
}

export function nowSentence(status: CallStatus, node: string | null): Bilingual {
  if (status === "waiting") {
    return { en: "Waiting for your call.", ja: "お電話をお待ちしています。" };
  }
  if (status === "ended") {
    return { en: "The call has ended. Here is what happened.", ja: "通話が終了しました。" };
  }
  return (
    (node ? NOW_SENTENCES[node] : undefined) ?? {
      en: `${nodeLabel(node ?? "greeting").en}.`,
      ja: nodeLabel(node ?? "greeting").ja,
    }
  );
}

export const COMPLIANCE_CHECKS: readonly {
  key: Exclude<keyof ComplianceUpdated, "type">;
  label: Bilingual;
  blockedReason: string;
}[] = [
  {
    key: "calling_hours",
    label: { en: "Calling hours", ja: "通話時間帯" },
    blockedReason: "Outside 08:00–21:00 Japan time, so the call was refused.",
  },
  {
    key: "identity_gate",
    label: { en: "Identity gate", ja: "本人確認" },
    blockedReason: "Identity could not be confirmed, so nothing about the account was shared.",
  },
  {
    key: "offer_within_terms",
    label: { en: "Offer inside terms", ja: "条件内の提案" },
    blockedReason: "The last offer was outside the terms and was not accepted.",
  },
  {
    key: "ai_disclosure",
    label: { en: "AI disclosure", ja: "AIであることの告知" },
    blockedReason: "",
  },
  {
    key: "recording_notice",
    label: { en: "Recording notice", ja: "記録の告知" },
    blockedReason: "",
  },
];

export function complianceSummary(compliance: ComplianceUpdated | null): string {
  if (compliance === null) {
    return "Waiting for the call to start.";
  }
  const statuses: CheckStatus[] = COMPLIANCE_CHECKS.map(({ key }) => compliance[key]);
  const passing = statuses.filter((status) => status === "pass").length;
  const blocked = statuses.filter((status) => status === "blocked").length;
  const blockedNote = blocked > 0 ? ` ${String(blocked)} guardrail stopped something.` : "";
  return `${String(passing)} of ${String(statuses.length)} safeguards holding.${blockedNote}`;
}
