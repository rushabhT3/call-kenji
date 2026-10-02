import { PipecatClient } from "@pipecat-ai/client-js";
import { SmallWebRTCTransport } from "@pipecat-ai/small-webrtc-transport";
import { useCallback, useEffect, useMemo, useState } from "react";
import { LINE_UNREACHABLE, microphoneProblem } from "./copy.ts";

export type BrowserCallState = "idle" | "connecting" | "connected" | "failed";

export const OFFER_ENDPOINT = "/api/offer";
export const ICE_ENDPOINT = "/api/ice";
const HOLD_MESSAGE = "hold";
// The server closes a call that has been silent too long; on Hold, the page says it is still here.
const HOLD_HEARTBEAT_MS = 15_000;

export interface BrowserCall {
  client: PipecatClient;
  state: BrowserCallState;
  isMuted: boolean;
  isOnHold: boolean;
  error: string | null;
  start: () => Promise<void>;
  end: () => Promise<void>;
  toggleMute: () => void;
  toggleHold: () => void;
}

async function fetchIceServers(): Promise<RTCIceServer[]> {
  const response = await fetch(ICE_ENDPOINT);
  if (!response.ok) {
    throw new Error(`ICE servers unavailable (${String(response.status)})`);
  }
  const body = (await response.json()) as { iceServers: RTCIceServer[] };
  return body.iceServers;
}

function createClient(): PipecatClient {
  return new PipecatClient({
    transport: new SmallWebRTCTransport(),
    enableMic: true,
    enableCam: false,
  });
}

/** Why the microphone cannot be used, or null once the browser has granted it. */
async function microphoneFailure(client: PipecatClient): Promise<string | null> {
  // A microphone that failed before is asked for again: the caller may have allowed it since.
  if (client.needsInit() || client.mediaState.mic.state === "error") {
    await client.initDevices();
  }
  const mic = client.mediaState.mic;
  return mic.state === "error" ? microphoneProblem(mic.reason) : null;
}

/** Dials Kenji, or says in plain words why the call could not be placed. */
async function placeCall(client: PipecatClient, viewerId: string | null): Promise<string | null> {
  try {
    // A call Kenji cannot hear is worse than no call, so it is not placed at all.
    const micFailure = await microphoneFailure(client);
    if (micFailure !== null) {
      return micFailure;
    }
    const iceServers = await fetchIceServers();
    await client.connect({
      webrtcRequestParams: { endpoint: OFFER_ENDPOINT, requestData: { viewer_id: viewerId } },
      iceConfig: { iceServers },
    });
    return null;
  } catch {
    return LINE_UNREACHABLE;
  }
}

export function useBrowserCall(viewerId: string | null): BrowserCall {
  const client = useMemo(() => createClient(), []);
  const [state, setState] = useState<BrowserCallState>("idle");
  const [isMuted, setIsMuted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const start = useCallback(async () => {
    setState("connecting");
    setError(null);
    const failure = await placeCall(client, viewerId);
    setState(failure === null ? "connected" : "failed");
    setError(failure);
  }, [client, viewerId]);

  const toggleMute = useCallback(() => {
    client.enableMic(isMuted);
    setIsMuted(!isMuted);
  }, [client, isMuted]);

  const hold = useHold(client);
  const end = useCallback(async () => {
    hold.reset();
    await client.disconnect();
    setState("idle");
  }, [client, hold]);

  return {
    client,
    state,
    isMuted,
    isOnHold: hold.isOn,
    error,
    start,
    end,
    toggleMute,
    toggleHold: hold.toggle,
  };
}

/** Hold keeps the caller's turn open on the server until they press Done. */
function useHold(client: PipecatClient) {
  const [isOn, setIsOn] = useState(false);

  useEffect(() => {
    if (!isOn) {
      return undefined;
    }
    const heartbeat = window.setInterval(() => {
      client.sendClientMessage(HOLD_MESSAGE, { on: true });
    }, HOLD_HEARTBEAT_MS);
    return () => {
      window.clearInterval(heartbeat);
    };
  }, [client, isOn]);

  const toggle = useCallback(() => {
    client.sendClientMessage(HOLD_MESSAGE, { on: !isOn });
    setIsOn(!isOn);
  }, [client, isOn]);

  const reset = useCallback(() => {
    setIsOn(false);
  }, []);

  return useMemo(() => ({ isOn, toggle, reset }), [isOn, toggle, reset]);
}
