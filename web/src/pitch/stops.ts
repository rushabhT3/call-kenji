import type { Placement } from "./camera.ts";

export type StopId =
  "problem" | "kenji" | "xray" | "speed" | "turns" | "rules" | "stack" | "proof" | "call";

export type FocusId = "turn" | "strategist" | "compliance";

export interface StopData {
  id: StopId;
  title: string;
  ja: string;
  placement: Placement;
}

export interface StepData {
  stop: StopId;
  focus?: FocusId;
  label: string;
}

/** The universe the camera flies over, in world pixels. */
export const WORLD = { width: 6400, height: 4200 };

export const CENTRE_BURST: Placement = { x: 3350, y: 2050, scale: 1, rotate: -3 };

/** Round the map clockwise from the top left, ending beside the burst in the middle. */
export const STOPS: readonly StopData[] = [
  {
    id: "problem",
    title: "The problem",
    ja: "課題",
    placement: { x: 1150, y: 800, scale: 1, rotate: -4 },
  },
  {
    id: "kenji",
    title: "Meet Kenji",
    ja: "ケンジ",
    placement: { x: 3000, y: 540, scale: 0.9, rotate: 3 },
  },
  {
    id: "xray",
    title: "The live X-ray",
    ja: "Xレイ",
    placement: { x: 5150, y: 1150, scale: 1.2, rotate: -2 },
  },
  {
    id: "speed",
    title: "0.7 s on a 2 to 6 s model",
    ja: "応答時間",
    placement: { x: 5300, y: 3250, scale: 1, rotate: 4 },
  },
  {
    id: "turns",
    title: "Japanese turn-taking",
    ja: "ターン",
    placement: { x: 3400, y: 3550, scale: 0.9, rotate: -3 },
  },
  {
    id: "rules",
    title: "Compliance as code",
    ja: "コンプライアンス",
    placement: { x: 1500, y: 3450, scale: 0.95, rotate: 3 },
  },
  {
    id: "stack",
    title: "The stack",
    ja: "技術",
    placement: { x: 650, y: 2250, scale: 0.85, rotate: -5 },
  },
  {
    id: "proof",
    title: "The proof",
    ja: "証拠",
    placement: { x: 1900, y: 2150, scale: 0.7, rotate: 2 },
  },
  {
    id: "call",
    title: "Your turn",
    ja: "あなたの番",
    placement: { x: 4700, y: 2200, scale: 0.75, rotate: -2 },
  },
];

/** Step 0 is the overview of the whole universe; these are steps 1 onwards. */
export const STEPS: readonly StepData[] = [
  { stop: "problem", label: "The problem" },
  { stop: "kenji", label: "Meet Kenji" },
  { stop: "xray", label: "The live X-ray" },
  { stop: "xray", focus: "turn", label: "Why he answered when he did" },
  { stop: "xray", focus: "strategist", label: "A second brain" },
  { stop: "xray", focus: "compliance", label: "The law, checked live" },
  { stop: "speed", label: "0.7 s on a 2 to 6 s model" },
  { stop: "turns", label: "Japanese turn-taking" },
  { stop: "rules", label: "Compliance as code" },
  { stop: "stack", label: "The stack" },
  { stop: "proof", label: "The proof" },
  { stop: "call", label: "Your turn" },
];

export const OVERVIEW_STEP = 0;
export const LAST_STEP = STEPS.length;

/** The first step that shows a stop, for flying there from the overview. */
export function firstStepOf(stop: StopId): number {
  return STEPS.findIndex((step) => step.stop === stop) + 1;
}

/** The step a "#3" address opens at, or the overview for anything else. */
export function stepFromHash(hash: string): number {
  const step = Number(hash.replace("#", ""));
  return Number.isInteger(step) && step >= OVERVIEW_STEP && step <= LAST_STEP
    ? step
    : OVERVIEW_STEP;
}

export function stepLabel(step: number): string {
  return step === OVERVIEW_STEP ? "The whole universe" : (STEPS[step - 1]?.label ?? "");
}
