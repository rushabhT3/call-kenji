export interface Recording {
  source: string;
  recorded_on: string;
  /** Both sides of the call's audio, beside the recording; replayed at normal speed only. */
  audio?: string;
  events: readonly { offset_ms: number; event: unknown }[];
}

export const DEMO_RECORDING_URL = "/demo/call.json";

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
