import { parseCallEvent, type CallEvent } from "../contract/events.ts";

export interface Recording {
  source: string;
  recorded_on: string;
  /** Both sides of the call's audio, beside the recording; replayed at normal speed only. */
  audio?: string;
  events: readonly { offset_ms: number; event: unknown }[];
}

export interface ScheduledEvent {
  delayMs: number;
  event: CallEvent;
}

export const DEMO_RECORDING_URL = "/demo/call.json";

export function replaySchedule(recording: Recording, speed: number): ScheduledEvent[] {
  if (speed <= 0) {
    throw new Error(`replay speed must be positive, got ${String(speed)}`);
  }
  return recording.events.flatMap(({ offset_ms, event }) => {
    const parsed = parseCallEvent(event);
    return parsed ? [{ delayMs: offset_ms / speed, event: parsed }] : [];
  });
}

export function startReplay(
  schedule: readonly ScheduledEvent[],
  onEvent: (event: CallEvent) => void,
): () => void {
  const timers = schedule.map(({ delayMs, event }) =>
    window.setTimeout(() => {
      onEvent(event);
    }, delayMs),
  );
  return () => {
    timers.forEach((timer) => {
      window.clearTimeout(timer);
    });
  };
}

export async function loadRecording(url: string = DEMO_RECORDING_URL): Promise<Recording> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`demo recording unavailable (${String(response.status)})`);
  }
  return (await response.json()) as Recording;
}

/** Where the recording's audio is, or null when it has none or plays too fast to hear. */
export function recordingAudioUrl(
  recording: Recording,
  speed: number,
  recordingUrl: string = DEMO_RECORDING_URL,
): string | null {
  if (!recording.audio || speed !== 1) {
    return null;
  }
  return new URL(recording.audio, new URL(recordingUrl, "http://page.invalid")).pathname;
}

export function replaySpeed(search: string): number {
  const speed = Number(new URLSearchParams(search).get("speed") ?? "1");
  return Number.isFinite(speed) && speed > 0 ? speed : 1;
}

export function isDemoMode(search: string): boolean {
  return new URLSearchParams(search).get("demo") === "1";
}
