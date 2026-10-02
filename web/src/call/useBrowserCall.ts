import { PipecatClient } from "@pipecat-ai/client-js";
import { SmallWebRTCTransport } from "@pipecat-ai/small-webrtc-transport";
import { useCallback, useMemo, useState } from "react";
import { LINE_UNREACHABLE, microphoneProblem } from "./copy.ts";

export type BrowserCallState = "idle" | "connecting" | "connected" | "failed";

export const OFFER_ENDPOINT = "/api/offer";
export const ICE_ENDPOINT = "/api/ice";

export interface BrowserCall {
  client: PipecatClient;
  state: BrowserCallState;
  isMuted: boolean;
  error: string | null;
  start: () => Promise<void>;
  end: () => Promise<void>;
  toggleMute: () => void;
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

export function useBrowserCall(viewerId: string | null): BrowserCall {
  const client = useMemo(() => createClient(), []);
  const [state, setState] = useState<BrowserCallState>("idle");
  const [isMuted, setIsMuted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fail = useCallback((message: string) => {
    setState("failed");
    setError(message);
  }, []);

  const start = useCallback(async () => {
    setState("connecting");
    setError(null);
    try {
      // A call Kenji cannot hear is worse than no call, so it is not placed at all.
      const micFailure = await microphoneFailure(client);
      if (micFailure !== null) {
        fail(micFailure);
        return;
      }
      const iceServers = await fetchIceServers();
      await client.connect({
        webrtcRequestParams: { endpoint: OFFER_ENDPOINT, requestData: { viewer_id: viewerId } },
        iceConfig: { iceServers },
      });
      setState("connected");
    } catch {
      fail(LINE_UNREACHABLE);
    }
  }, [client, viewerId, fail]);

  const end = useCallback(async () => {
    await client.disconnect();
    setState("idle");
  }, [client]);

  const toggleMute = useCallback(() => {
    client.enableMic(isMuted);
    setIsMuted(!isMuted);
  }, [client, isMuted]);

  return { client, state, isMuted, error, start, end, toggleMute };
}
