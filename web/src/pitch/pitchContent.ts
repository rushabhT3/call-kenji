export interface Card {
  title: string;
  text: string;
}

export const PROBLEMS: readonly Card[] = [
  {
    title: "Turn-taking",
    text: "Callers say はい and ええ all the time while the other person talks, and a pause after 「生年月日は、」 is not the end of a turn.",
  },
  {
    title: "Compliance",
    text: "An identity check before any account detail, payment terms the model cannot bend, and every request to stop calling recorded.",
  },
  {
    title: "Latency",
    text: "Every reply is split into end of turn, model and voice, and timed against a 1,500 ms budget.",
  },
];

export interface Exchange {
  ja: string;
  en: string;
}

/** Kenji's real opening, from the recorded demo call, with its own subtitle. */
export const GREETING: Exchange = {
  ja: "お電話ありがとうございます。みなとのAIアシスタント、ケンジと申します。こちらはデモ用の通話です。",
  en: "Thank you for calling. I'm Kenji, an AI assistant at Minato. This is a demo call.",
};

export const KENJI_FACTS: readonly string[] = [
  "Speaks Japanese, and says he is an AI before anything else",
  "Five fictional callers to play, each with their own debt and story",
  "No Japanese needed: Say it plays your lines into the call",
  "Every decision on screen while you talk, for your call only",
];

/** The real refusal from the recorded demo call, with its own subtitles. */
export const REFUSAL: { caller: Exchange; kenji: Exchange } = {
  caller: {
    ja: "今月はちょっと厳しくて、月3,000円なら払えます。",
    en: "This month's tight, but I can pay 3,000 yen a month.",
  },
  kenji: {
    ja: "申し訳ございません。毎月3,000円ですと、お受けできる条件に届きません。毎月6,000円からでしたらお受けできますが、いかがでしょうか。",
    en: "I'm sorry, ¥3,000 a month is below what we can accept. We can accept from ¥6,000 a month. Would that work for you?",
  },
};

export interface Safeguard {
  name: string;
  ja: string;
}

export const SAFEGUARDS: readonly Safeguard[] = [
  { name: "Calling hours", ja: "通話時間帯" },
  { name: "Identity gate", ja: "本人確認" },
  { name: "Offer inside terms", ja: "条件内の提案" },
  { name: "AI disclosure", ja: "AIであることの告知" },
  { name: "Recording notice", ja: "記録の告知" },
];

export const EVIDENCE: readonly string[] = [
  "600+ Python tests, the rules at 100% line and branch coverage",
  "120+ web unit tests and 80+ browser tests, with WCAG AA scans",
  "24 of 24 real-model conversations after every behaviour change",
  "Strict mypy, Ruff and ESLint, CI on every push to main",
];

export interface Destination {
  label: string;
  href: string;
  isPrimary?: boolean;
}

export const DESTINATIONS: readonly Destination[] = [
  { label: "Call Kenji", href: "/#call", isPrimary: true },
  { label: "Watch a real call", href: "/?demo=1" },
  { label: "How it's built", href: "/features" },
  { label: "The trailer", href: "/trailer" },
];
