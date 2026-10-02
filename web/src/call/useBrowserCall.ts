import { PipecatClient } from "@pipecat-ai/client-js";
import { SmallWebRTCTransport } from "@pipecat-ai/small-webrtc-transport";
import { useCallback, useMemo, useState } from "react";

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

export function useBrowserCall(viewerId: string | null): BrowserCall {
  const client = useMemo(() => createClient(), []);
  const [state, setState] = useState<BrowserCallState>("idle");
  const [isMuted, setIsMuted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const start = useCallback(async () => {
    setState("connecting");
    setError(null);
    try {
      const iceServers = await fetchIceServers();
      await client.connect({
        webrtcRequestParams: { endpoint: OFFER_ENDPOINT, requestData: { viewer_id: viewerId } },
        iceConfig: { iceServers },
      });
      setState("connected");
    } catch (cause) {
      setState("failed");
      setError(cause instanceof Error ? cause.message : "The call could not start.");
    }
  }, [client, viewerId]);

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
