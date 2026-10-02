import type {
  AuditPublished,
  CallEvent,
  CallOutcome,
  ComplianceUpdated,
  HandoffRecorded,
  LatencyMeasured,
  SmsPreview,
  Speaker,
  StrategistUpdated,
  Transport,
  TurnAssessed,
} from "../contract/events.ts";

export type CallStatus = "waiting" | "live" | "ended";

export interface TranscriptEntry {
  lineId: string;
  speaker: Speaker;
  ja: string;
  isBackchannel: boolean;
  at: string;
}

export interface PartialLine {
  lineId: string;
  ja: string;
}

export interface CallView {
  status: CallStatus;
  transport: Transport | null;
  startedAt: string | null;
  endedAt: string | null;
  node: string | null;
  lines: TranscriptEntry[];
  partial: PartialLine | null;
  subtitles: Readonly<Record<string, string>>;
  turn: TurnAssessed | null;
  strategist: StrategistUpdated | null;
  compliance: ComplianceUpdated | null;
  latency: LatencyMeasured[];
  handoff: HandoffRecorded | null;
  sms: SmsPreview | null;
  outcome: CallOutcome | null;
  audit: AuditPublished | null;
}

export const EMPTY_CALL: CallView = {
  status: "waiting",
  transport: null,
  startedAt: null,
  endedAt: null,
  node: null,
  lines: [],
  partial: null,
  subtitles: {},
  turn: null,
  strategist: null,
  compliance: null,
  latency: [],
  handoff: null,
  sms: null,
  outcome: null,
  audit: null,
};

function withTranscript(
  view: CallView,
  event: Extract<CallEvent, { type: "transcript" }>,
): CallView {
  if (!event.is_final) {
    return { ...view, partial: { lineId: event.line_id, ja: event.ja } };
  }
  const entry: TranscriptEntry = {
    lineId: event.line_id,
    speaker: event.speaker,
    ja: event.ja,
    isBackchannel: event.is_backchannel,
    at: event.at,
  };
  const others = view.lines.filter((line) => line.lineId !== event.line_id);
  const partial = view.partial?.lineId === event.line_id ? null : view.partial;
  return { ...view, lines: [...others, entry], partial };
}

export function applyEvent(view: CallView, event: CallEvent): CallView {
  switch (event.type) {
    case "call_started":
      return { ...view, status: "live", transport: event.transport, startedAt: event.started_at };
    case "transcript":
      return withTranscript(view, event);
    case "subtitle":
      return { ...view, subtitles: { ...view.subtitles, [event.line_id]: event.en } };
    case "flow_node":
      return { ...view, node: event.node };
    case "turn":
      return { ...view, turn: event };
    case "strategist":
      return { ...view, strategist: event };
    case "compliance":
      return { ...view, compliance: event };
    case "latency":
      return { ...view, latency: [...view.latency, event] };
    case "handoff":
      return { ...view, handoff: event };
    case "sms_preview":
      return { ...view, sms: event };
    case "call_ended":
      return {
        ...view,
        status: "ended",
        outcome: event.outcome,
        endedAt: event.ended_at,
        partial: null,
      };
    case "audit":
      return { ...view, audit: event };
  }
}

export function applyEvents(view: CallView, events: readonly CallEvent[]): CallView {
  return events.reduce(applyEvent, view);
}

export function latestKenjiLineId(view: CallView): string | null {
  const kenjiLines = view.lines.filter((line) => line.speaker === "kenji");
  return kenjiLines.at(-1)?.lineId ?? null;
}

export function elapsedMs(from: string, to: string): number {
  return Math.max(0, Date.parse(to) - Date.parse(from));
}
