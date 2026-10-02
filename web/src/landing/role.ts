/** The fictional debtor the visitor plays. Mirrors content/account.yaml (checked by a test). */
export const ROLE = {
  nameJa: "佐藤ゆうき",
  nameEn: "Yuki Sato",
  dateOfBirth: "1990-07-14",
  dateOfBirthJa: "平成2年7月14日",
  accountSuffix: "7731",
  balanceYen: 35000,
  overdueSince: "2026-09-30",
} as const;

export interface Suggestion {
  ja: string;
  en: string;
}

export const THINGS_TO_TRY: readonly Suggestion[] = [
  { ja: "佐藤ゆうきです。平成2年7月14日生まれです。", en: "Confirm who you are when Kenji asks." },
  {
    ja: "毎月3,000円なら払えます。",
    en: "Offer too little and hear how Kenji stays inside the terms.",
  },
  {
    ja: "佐藤の家族ですが…",
    en: "Pretend to be a relative. Kenji should say nothing about the debt.",
  },
  { ja: "担当者と話したいです。", en: "Ask for a person and get a handoff record." },
  { ja: "もう電話しないでください。", en: "Ask Kenji to stop contacting you." },
];
