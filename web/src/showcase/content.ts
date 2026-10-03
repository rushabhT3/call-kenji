export interface Stat {
  value: number;
  decimals: number;
  prefix?: string;
  suffix?: string;
  label: string;
}

export const STATS: readonly Stat[] = [
  {
    value: 0.7,
    decimals: 1,
    suffix: " s",
    label: "to Kenji's first audio after you finish (p50, real calls)",
  },
  { value: 24, decimals: 0, suffix: "/24", label: "real-model conversations passed" },
  { value: 100, decimals: 0, suffix: "%", label: "line and branch coverage on the rules" },
  { value: 14, decimals: 0, label: "live event types behind the X-ray" },
  { value: 52, decimals: 0, label: "design decisions, written down" },
];

export interface Screenshot {
  src: string;
  width: number;
  height: number;
  alt: string;
}

export interface XrayCallout {
  id: string;
  title: string;
  ja: string;
  text: string;
  shot: Screenshot;
}

export const XRAY_DESKTOP: Screenshot = {
  src: "/showcase/xray-desktop.webp",
  width: 2880,
  height: 2000,
  alt: "The X-ray near the end of a recorded call: the transcript in Japanese with English underneath, and the caller's card, the Turn card and the Strategist card on the right.",
};

export const XRAY_PHONE: Screenshot = {
  src: "/showcase/xray-phone.webp",
  width: 780,
  height: 1688,
  alt: "The X-ray on a phone near the end of a recorded call.",
};

export const XRAY_CALLOUTS: readonly XrayCallout[] = [
  {
    id: "transcript",
    title: "Every word, as it's said",
    ja: "通話記録",
    text: "Japanese as it is spoken, English underneath, and Kenji's line on screen the moment he starts saying it.",
    shot: {
      src: "/showcase/card-transcript.webp",
      width: 1690,
      height: 1768,
      alt: "Transcript card: Kenji reads back the payment plan, the caller agrees, and Kenji closes the call.",
    },
  },
  {
    id: "turn",
    title: "Why he answered when he did",
    ja: "ターン",
    text: "Smart Turn's reading of your voice, and whether a はい was agreement or just politeness.",
    shot: {
      src: "/showcase/card-turn.webp",
      width: 952,
      height: 296,
      alt: "Turn card: Smart Turn was 88% sure you had finished, so Kenji answered.",
    },
  },
  {
    id: "strategist",
    title: "A second brain, never in the way",
    ja: "戦略",
    text: "Another model reads every turn and plans the next move. Kenji gets its advice on the following turn, so the reply never waits.",
    shot: {
      src: "/showcase/card-strategist.webp",
      width: 952,
      height: 1218,
      alt: "Strategist card: next move, identity verified, the caller's situation, ability to pay and three offers inside the terms.",
    },
  },
  {
    id: "compliance",
    title: "The law, checked live",
    ja: "コンプライアンス",
    text: "Calling hours, the identity gate, the payment terms, the AI disclosure and the recording notice, each shown as it holds.",
    shot: {
      src: "/showcase/card-compliance.webp",
      width: 952,
      height: 1046,
      alt: "Compliance card: all five safeguards passing, with the call's time in Tokyo inside 08:00 to 21:00.",
    },
  },
  {
    id: "latency",
    title: "Every millisecond, in the open",
    ja: "応答時間",
    text: "End of turn, model and voice for every reply, against a 1,500 ms budget, with p50 and p95.",
    shot: {
      src: "/showcase/card-latency.webp",
      width: 952,
      height: 1274,
      alt: "Latency card: the last reply inside the 1,500 ms budget, split into end of turn, model and first audio, with p50 and p95.",
    },
  },
];

export interface SpeedTrick {
  title: string;
  text: string;
}

export const SPEED_TRICKS: readonly SpeedTrick[] = [
  {
    title: "Don't ask the model what the rules already know.",
    text: "A full name and birthday, an amount, a plain yes: the fast path answers these from rules, through the same tools the model would call, so the audit and every compliance check still run.",
  },
  {
    title: "Say 「はい、」 first.",
    text: "Every other turn opens with an instant 「はい、」 while the model thinks. Kenji keeps the floor until his answer plays, so your polite はい can't cancel it.",
  },
  {
    title: "Race the slow tail.",
    text: "A request that hasn't streamed after 2.5 s is raced by an identical one. The first to speak wins, and the loser is closed before any of it is used.",
  },
  {
    title: "Keep the second brain off the critical path.",
    text: "The strategist writes structured advice after each of your turns. Kenji reads it on the next one, so the reply never waits for it.",
  },
  {
    title: "Never go silent.",
    text: "If the model says nothing for 8 s, Kenji says 「少々お待ちください。」 and tries the model once more. If that is silent too, he apologises, asks you to say it again and hands the turn back.",
  },
];

export interface EventRoute {
  card: string;
  events: readonly string[];
}

export const EVENT_ROUTES: readonly EventRoute[] = [
  { card: "Header and your card", events: ["call_started"] },
  { card: "Transcript", events: ["transcript", "subtitle", "caller_tone"] },
  { card: "Now and your hints", events: ["flow_node"] },
  { card: "Turn", events: ["turn", "turn_end"] },
  { card: "Strategist", events: ["strategist", "caller_tone"] },
  { card: "Compliance", events: ["compliance"] },
  { card: "Latency", events: ["latency"] },
  {
    card: "After the call",
    events: ["call_ended", "handoff", "sms_preview", "audit"],
  },
];
