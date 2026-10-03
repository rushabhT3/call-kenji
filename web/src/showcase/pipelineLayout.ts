/** Where each part of the pipeline map sits: rows stack top to bottom inside a 340-wide panel. */
import type { LabelledBoxProps } from "./svg/LabelledBox.tsx";

interface Row {
  y: number;
  height: number;
}

const ROW_GAP = 20;
const TOOLS_GAP = 28;
const SIDE_GAP = 10;
const FRAME_PADDING = 16;
const FRAME_HEADER = 54;
const SIDE_LABEL_DROP = 28;
const SIDE_LABEL_TO_BOXES = 12;
const BOTTOM_MARGIN = 24;
const CALLER_WIDTH = 130;
const WORKER_WIDTH = 116;
const HALF_WIDTH = 116;
const DOMAIN_WIDTH = 150;

function below(row: Row, height: number, gap = ROW_GAP): Row {
  return { y: row.y + row.height + gap, height };
}

const CALLER_ROW: Row = { y: 60, height: 64 };
const WORKER_ROW = below(CALLER_ROW, 80, FRAME_PADDING);
const FRAME_TOP = WORKER_ROW.y + WORKER_ROW.height + FRAME_PADDING;
const HEARING_ROW: Row = { y: FRAME_TOP + FRAME_HEADER, height: 48 };
const TURNS_ROW = below(HEARING_ROW, 62);
const SPLIT_ROW = below(TURNS_ROW, 82);
const DOMAIN_ROW = below(SPLIT_ROW, 94, TOOLS_GAP);
const KANA_ROW = below(DOMAIN_ROW, 40);
const VOICE_ROW = below(KANA_ROW, 40);
export const SIDE_LABEL_Y = VOICE_ROW.y + VOICE_ROW.height + SIDE_LABEL_DROP;
const STRATEGIST_ROW: Row = { y: SIDE_LABEL_Y + SIDE_LABEL_TO_BOXES, height: 46 };
const TONE_ROW = below(STRATEGIST_ROW, 46, SIDE_GAP);
const SUBTITLE_ROW = below(TONE_ROW, 46, SIDE_GAP);

export const FRAME = {
  x: 16,
  y: FRAME_TOP,
  width: 280,
  height: SUBTITLE_ROW.y + SUBTITLE_ROW.height + FRAME_PADDING - FRAME_TOP,
} as const;
const OUTPUT_ROW: Row = { y: FRAME.y + FRAME.height + ROW_GAP, height: 56 };
export const HEIGHT = OUTPUT_ROW.y + OUTPUT_ROW.height + BOTTOM_MARGIN;

export const INNER = { x: 36, width: 248 } as const;
export const SIDE_RAIL_X = 26;
export const RETURN_X = 314;
/** Browser audio goes to the server directly (WebRTC, TURN relay if needed), past the Worker. */
export const BROWSER_AUDIO_X = 140;
/** Each answer path's line down to the kana normaliser runs outside the domain box. */
export const SPEECH_INSET = 24;

export const BROWSER: LabelledBoxProps = {
  step: 1,
  x: 16,
  ...CALLER_ROW,
  width: CALLER_WIDTH,
  title: ["Browser"],
  detail: ["WebRTC"],
  tone: "paper",
};
export const PHONE: LabelledBoxProps = {
  step: 2,
  x: 160,
  ...CALLER_ROW,
  width: CALLER_WIDTH,
  title: ["Phone"],
  detail: ["Twilio", "Media Streams"],
  tone: "paper",
};
export const WORKER: LabelledBoxProps = {
  step: 3,
  x: 16,
  ...WORKER_ROW,
  width: WORKER_WIDTH,
  title: ["Cloudflare", "Worker"],
  detail: ["page, signalling,", "live events"],
};
export const HEARING: LabelledBoxProps = {
  step: 5,
  ...INNER,
  ...HEARING_ROW,
  title: ["Silero VAD + Soniox STT"],
  detail: ["Japanese"],
};
export const TURNS: LabelledBoxProps = {
  step: 6,
  ...INNER,
  ...TURNS_ROW,
  title: ["Turn handling"],
  detail: ["Soniox endpoint + Smart Turn v3", "+ particle rule + Hold"],
};
export const FAST_PATH: LabelledBoxProps = {
  step: 7,
  x: INNER.x,
  ...SPLIT_ROW,
  width: HALF_WIDTH,
  title: ["Fast path"],
  detail: ["rules answer", "predictable turns"],
  tone: "green",
};
export const TALKER: LabelledBoxProps = {
  step: 8,
  x: INNER.x + INNER.width - HALF_WIDTH,
  ...SPLIT_ROW,
  width: HALF_WIDTH,
  title: ["Talker"],
  detail: ["Muse Spark,", "Pipecat Flows", "steps + tools"],
  tone: "blue",
};
export const DOMAIN: LabelledBoxProps = {
  step: 9,
  x: INNER.x + (INNER.width - DOMAIN_WIDTH) / 2,
  ...DOMAIN_ROW,
  width: DOMAIN_WIDTH,
  title: ["Domain rules"],
  detail: ["identity · terms", "calling hours", "stop-contact", "pure, 100% tested"],
  shadow: "red",
};
export const KANA: LabelledBoxProps = {
  step: 10,
  ...INNER,
  ...KANA_ROW,
  title: ["Kana normaliser"],
};
export const VOICE: LabelledBoxProps = {
  step: 11,
  ...INNER,
  ...VOICE_ROW,
  title: ["Cartesia Sonic TTS"],
  tone: "orange",
};

export const SIDE_LANE: readonly LabelledBoxProps[] = [
  {
    step: 13,
    ...INNER,
    ...STRATEGIST_ROW,
    title: ["Strategist · Muse Spark"],
    detail: ["JSON advice for the next turn"],
    tone: "teal",
  },
  {
    step: 14,
    ...INNER,
    ...TONE_ROW,
    title: ["SenseVoice"],
    detail: ["how you sound"],
    tone: "teal",
  },
  {
    step: 15,
    ...INNER,
    ...SUBTITLE_ROW,
    title: ["Translator"],
    detail: ["English subtitles"],
    tone: "teal",
  },
];

export const EVENTS: LabelledBoxProps = {
  step: 16,
  x: 16,
  ...OUTPUT_ROW,
  width: 164,
  title: ["Events → your X-ray"],
  detail: ["WebSocket, only your tab"],
  tone: "paper",
  shadow: "red",
};
export const AUDIT: LabelledBoxProps = {
  step: 17,
  x: 196,
  ...OUTPUT_ROW,
  width: 100,
  title: ["Audit log"],
  detail: ["hash-chained"],
};
