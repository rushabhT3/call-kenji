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

/**
 * Keep each WebRTC offer a browser call sends, then refuse it, so a test can read what the page
 * told the voice server. Register after routeViewerFeed: later routes are tried first.
 */
export async function captureOffers(page: Page): Promise<unknown[]> {
  const offers: unknown[] = [];
  await page.route("**/api/ice", (route) => route.fulfill({ json: { iceServers: [] } }));
  await page.route("**/api/offer", async (route) => {
    offers.push(route.request().postDataJSON());
    await route.abort();
  });
  return offers;
}

interface Recording {
  events: { offset_ms: number; event: { type: string } }[];
}

const HANDOFF_EVENT = {
  type: "handoff",
  reason: "担当者と話したい",
  summary: "Verified caller asked to speak to a person about the plan.",
  identity_status: "verified",
  node: "negotiate",
  requested_at: "2026-10-03T15:02:10+09:00",
};

const TURN_EVENT = {
  type: "turn",
  node: "read_back",
  utterance: "はい",
  overlap_ms: 420,
  characters: 2,
  score: 0,
  threshold: 0.85,
  verdict: "backchannel",
};

function withEveryCard(recording: Recording): Recording {
  const endIndex = recording.events.findIndex(({ event }) => event.type === "call_ended");
  const offsetMs = recording.events[endIndex - 1]?.offset_ms ?? 0;
  const events = [...recording.events];
  const added = [HANDOFF_EVENT, TURN_EVENT].map((event) => ({ offset_ms: offsetMs, event }));
  events.splice(endIndex, 0, ...added);
  return { ...recording, events };
}

/**
 * The demo replays a real call that ended in a promise with nobody talking over Kenji, so it has
 * no handoff and no turn decision. Serve it with one of each so every card's numbers can be checked.
 */
export async function serveRecordingWithEveryCard(page: Page): Promise<void> {
  await page.route("**/demo/call.json", async (route) => {
    const response = await route.fetch();
    const recording = (await response.json()) as Recording;
    await route.fulfill({ response, json: withEveryCard(recording) });
  });
}

/** The recorded call lasts about 115 s: speed 4 leaves time to inspect it mid-call. */
export const MID_CALL_URL = "/?demo=1&speed=4";
export const DEMO_URL = "/?demo=1&speed=40";
/** At normal speed the replay has its sound, and waits for the visitor to press Play. */
export const PLAYER_URL = "/?demo=1";
export const WIDTHS = [1440, 1024, 768, 390] as const;
const REPLAY_TIMEOUT_MS = 20_000;
// A live transcript shows the latest three lines, so three lines in means the call is well under way.
const LINES_BEFORE_INSPECTING = 3;

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

/** Open the demo at normal speed, once its waveform is drawn and Play can start the sound. */
export async function openPlayer(page: Page): Promise<void> {
  await page.goto(PLAYER_URL);
  await expect(page.getByText("Press Play to hear both voices")).toBeVisible({
    timeout: REPLAY_TIMEOUT_MS,
  });
}
