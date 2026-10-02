import { PipecatClient } from "@pipecat-ai/client-js";
import { SmallWebRTCTransport } from "@pipecat-ai/small-webrtc-transport";
import { useCallback, useMemo, useState } from "react";

export type BrowserCallState = "idle" | "connecting" | "connected" | "failed";

export const OFFER_ENDPOINT = "/api/offer";
const STUN_SERVERS: RTCIceServer[] = [{ urls: "stun:stun.l.google.com:19302" }];

export interface BrowserCall {
  client: PipecatClient;
  state: BrowserCallState;
  isMuted: boolean;
  error: string | null;
  start: () => Promise<void>;
  end: () => Promise<void>;
  toggleMute: () => void;
}

function createClient(): PipecatClient {
  return new PipecatClient({
    transport: new SmallWebRTCTransport({ iceServers: STUN_SERVERS }),
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
      await client.connect({
        webrtcRequestParams: { endpoint: OFFER_ENDPOINT, requestData: { viewer_id: viewerId } },
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
