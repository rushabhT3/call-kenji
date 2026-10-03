/**
 * Server-to-browser events for one call. Mirrors src/kenji/app/events.py; the demo
 * recording and the parser tests keep the two sides in step.
 */

export type CheckStatus = "pass" | "blocked" | "pending";
export type Speaker = "caller" | "kenji";
export type Transport = "phone" | "browser";
export type IdentityStatus = "unverified" | "verified" | "locked_out";
export type TurnVerdict = "backchannel" | "interruption";
export type CallOutcome =
  | "promise_to_pay"
  | "human_handoff"
  | "stop_contact"
  | "callback_requested"
  | "identity_not_verified"
  | "daily_limit_reached"
  | "no_agreement";

export interface CallStarted {
  type: "call_started";
  call_id: string;
  transport: Transport;
  started_at: string;
  /** The persona the caller plays, from /personas.json; absent in older recordings. */
  persona_id?: string | null;
}

export interface TranscriptLine {
  type: "transcript";
  line_id: string;
  speaker: Speaker;
  ja: string;
  is_final: boolean;
  is_backchannel: boolean;
  at: string;
}

export interface Subtitle {
  type: "subtitle";
  line_id: string;
  en: string;
  /** The translation failed for good: the line keeps its Japanese only. */
  is_unavailable?: boolean;
}

/** How the caller's voice sounded on a turn, as a speech-emotion model hears it. */
export type CallerEmotion =
  "neutral" | "happy" | "sad" | "angry" | "fearful" | "disgusted" | "surprised" | "unknown";
export type CallerSound = "laughter" | "crying" | "coughing" | "sneezing";

export interface CallerToneHeard {
  type: "caller_tone";
  /** The caller's transcript line this turn's tone belongs to. */
  line_id: string;
  emotion: CallerEmotion;
  sounds: CallerSound[];
}

export interface FlowNodeEntered {
  type: "flow_node";
  node: string;
}

export interface TurnAssessed {
  type: "turn";
  node: string;
  utterance: string;
  overlap_ms: number;
  characters: number;
  score: number;
  threshold: number;
  verdict: TurnVerdict;
}

/** Why Kenji waited to answer after the speech service said the caller had finished. */
export type TurnEndWait = "none" | "unfinished_phrase" | "still_talking" | "caller_hold";

export interface TurnEndJudged {
  type: "turn_end";
  /** Smart Turn's reading of the caller's voice: how likely they had finished; null with none. */
  finished_probability: number | null;
  waited_for: TurnEndWait;
  waited_ms: number;
}

export interface StrategistUpdated {
  type: "strategist";
  identity: string;
  situation: string;
  ability_to_pay: string;
  offers: string[];
  next_move: string;
}

export interface ComplianceUpdated {
  type: "compliance";
  calling_hours: CheckStatus;
  identity_gate: CheckStatus;
  offer_within_terms: CheckStatus;
  ai_disclosure: CheckStatus;
  recording_notice: CheckStatus;
  /** What the calling-hours rule means at the hour of the call; absent in older recordings. */
  calling_hours_note?: string;
}

/** How Kenji opened a reply: rules alone, an instant 「はい、」 while the model worked, or the model. */
export type Opening = "rules" | "acknowledgement" | "model";

export interface LatencyMeasured {
  type: "latency";
  turn: number;
  end_of_turn_ms: number;
  llm_first_token_ms: number;
  tts_first_audio_ms: number;
  total_ms: number;
  p50_ms: number;
  p95_ms: number;
  budget_ms: number;
  opened_with?: Opening;
}

export interface HandoffRecorded {
  type: "handoff";
  reason: string;
  summary: string;
  identity_status: IdentityStatus;
  node: string;
  requested_at: string;
}

export interface SmsPreview {
  type: "sms_preview";
  ja: string;
  en: string;
  is_sent: false;
}

export interface CallEnded {
  type: "call_ended";
  outcome: CallOutcome;
  ended_at: string;
}

export interface AuditPublished {
  type: "audit";
  is_chain_valid: boolean;
  head_hash: string;
  records: Record<string, unknown>[];
}

export type CallEvent =
  | CallStarted
  | TranscriptLine
  | Subtitle
  | CallerToneHeard
  | FlowNodeEntered
  | TurnAssessed
  | TurnEndJudged
  | StrategistUpdated
  | ComplianceUpdated
  | LatencyMeasured
  | HandoffRecorded
  | SmsPreview
  | CallEnded
  | AuditPublished;

export interface ViewerReady {
  type: "viewer_ready";
  viewer_id: string;
  code: string;
}

type FieldKind = "string" | "number" | "boolean" | "array";

const REQUIRED_FIELDS: Record<CallEvent["type"], Record<string, FieldKind>> = {
  call_started: { call_id: "string", transport: "string", started_at: "string" },
  transcript: {
    line_id: "string",
    speaker: "string",
    ja: "string",
    is_final: "boolean",
    is_backchannel: "boolean",
    at: "string",
  },
  subtitle: { line_id: "string", en: "string" },
  caller_tone: { line_id: "string", emotion: "string", sounds: "array" },
  flow_node: { node: "string" },
  turn: {
    node: "string",
    utterance: "string",
    overlap_ms: "number",
    characters: "number",
    score: "number",
    threshold: "number",
    verdict: "string",
  },
  turn_end: { waited_for: "string", waited_ms: "number" },
  strategist: {
    identity: "string",
    situation: "string",
    ability_to_pay: "string",
    offers: "array",
    next_move: "string",
  },
  compliance: {
    calling_hours: "string",
    identity_gate: "string",
    offer_within_terms: "string",
    ai_disclosure: "string",
    recording_notice: "string",
  },
  latency: {
    turn: "number",
    end_of_turn_ms: "number",
    llm_first_token_ms: "number",
    tts_first_audio_ms: "number",
    total_ms: "number",
    p50_ms: "number",
    p95_ms: "number",
    budget_ms: "number",
  },
  handoff: {
    reason: "string",
    summary: "string",
    identity_status: "string",
    node: "string",
    requested_at: "string",
  },
  sms_preview: { ja: "string", en: "string", is_sent: "boolean" },
  call_ended: { outcome: "string", ended_at: "string" },
  audit: { is_chain_valid: "boolean", head_hash: "string", records: "array" },
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasKind(value: unknown, kind: FieldKind): boolean {
  return kind === "array" ? Array.isArray(value) : typeof value === kind;
}

function isEventType(type: unknown): type is CallEvent["type"] {
  return typeof type === "string" && Object.hasOwn(REQUIRED_FIELDS, type);
}

export function parseCallEvent(raw: unknown): CallEvent | null {
  if (!isRecord(raw) || !isEventType(raw.type)) {
    return null;
  }
  const fields = Object.entries(REQUIRED_FIELDS[raw.type]);
  const isComplete = fields.every(([name, kind]) => hasKind(raw[name], kind));
  return isComplete ? (raw as unknown as CallEvent) : null;
}

export function parseViewerReady(raw: unknown): ViewerReady | null {
  if (!isRecord(raw) || raw.type !== "viewer_ready") {
    return null;
  }
  const isComplete = typeof raw.viewer_id === "string" && typeof raw.code === "string";
  return isComplete ? (raw as unknown as ViewerReady) : null;
}
