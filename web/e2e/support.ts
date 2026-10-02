import { expect, type Page, type WebSocketRoute } from "@playwright/test";

const BACKEND_HTTP = /\/(api|ws|start|sessions)\b/;

/** Abort every request to the voice server so a test proves the page needs no backend. */
export async function blockBackend(page: Page): Promise<string[]> {
  const attempts: string[] = [];
  await page.route(BACKEND_HTTP, async (route) => {
    attempts.push(route.request().url());
    await route.abort();
  });
  await page.routeWebSocket(/.*/, (socket) => {
    attempts.push(socket.url());
    void socket.close();
  });
  return attempts;
}

export interface FakeViewerFeed {
  connected: Promise<WebSocketRoute>;
}

/** Stand in for the voice server's private viewer feed, with no backend behind it. */
export async function routeViewerFeed(page: Page): Promise<FakeViewerFeed> {
  await page.route(BACKEND_HTTP, (route) => route.abort());
  let resolveConnected: (socket: WebSocketRoute) => void = () => undefined;
  const connected = new Promise<WebSocketRoute>((resolve) => {
    resolveConnected = resolve;
  });
  await page.routeWebSocket(/\/ws\/viewer$/, (socket) => {
    resolveConnected(socket);
  });
  return { connected };
}

export function sendViewerReady(socket: WebSocketRoute, code: string): void {
  socket.send(JSON.stringify({ type: "viewer_ready", viewer_id: "viewer-1", code }));
}

interface Recording {
  events: { offset_ms: number; event: { type: string } }[];
}

const MEASURED_EVENTS = [
  {
    type: "turn",
    node: "read_back",
    utterance: "はい",
    overlap_ms: 420,
    characters: 2,
    score: 0,
    threshold: 0.85,
    verdict: "backchannel",
  },
  {
    type: "latency",
    turn: 1,
    end_of_turn_ms: 310,
    llm_first_token_ms: 640,
    tts_first_audio_ms: 180,
    total_ms: 1130,
    p50_ms: 1130,
    p95_ms: 1130,
    budget_ms: 1500,
  },
  {
    type: "latency",
    turn: 2,
    end_of_turn_ms: 350,
    llm_first_token_ms: 980,
    tts_first_audio_ms: 240,
    total_ms: 1570,
    p50_ms: 1350,
    p95_ms: 1548,
    budget_ms: 1500,
  },
  {
    type: "handoff",
    reason: "担当者と話したい",
    summary: "Verified caller asked to speak to a person about the plan.",
    identity_status: "verified",
    node: "negotiate",
    requested_at: "2026-10-02T15:03:10+09:00",
  },
];

function withMeasurements(recording: Recording): Recording {
  const endIndex = recording.events.findIndex(({ event }) => event.type === "call_ended");
  const offsetMs = recording.events[endIndex - 1]?.offset_ms ?? 0;
  const added = MEASURED_EVENTS.map((event) => ({ offset_ms: offsetMs, event }));
  const events = [...recording.events];
  events.splice(endIndex, 0, ...added);
  return { ...recording, events };
}

/**
 * The scripted demo recording has no audio, so it carries no turn, latency or handoff events.
 * Serve it with a few added so the cards that show those numbers render populated.
 */
export async function serveMeasuredRecording(page: Page): Promise<void> {
  await page.route("**/demo/call.json", async (route) => {
    const response = await route.fetch();
    const recording = (await response.json()) as Recording;
    await route.fulfill({ response, json: withMeasurements(recording) });
  });
}

/** A replay slow enough to inspect while it is still running. */
export const MID_CALL_URL = "/?demo=1&speed=0.25";
export const DEMO_URL = "/?demo=1&speed=4";
export const WIDTHS = [1440, 1024, 768, 390] as const;
const REPLAY_TIMEOUT_MS = 20_000;
const LINES_BEFORE_INSPECTING = 4;

export async function openMidCall(page: Page): Promise<void> {
  await page.goto(MID_CALL_URL);
  await expect(
    page
      .getByRole("log")
      .getByRole("listitem")
      .nth(LINES_BEFORE_INSPECTING - 1),
  ).toBeVisible({ timeout: REPLAY_TIMEOUT_MS });
}

export async function openAfterCall(page: Page): Promise<void> {
  await page.goto(DEMO_URL);
  await expect(page.getByRole("heading", { name: /What happened/ })).toBeVisible({
    timeout: REPLAY_TIMEOUT_MS,
  });
}
