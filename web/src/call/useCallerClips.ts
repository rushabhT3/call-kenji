import { RTVIEvent, type PipecatClient } from "@pipecat-ai/client-js";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createClipMixer, sendAsMicrophone, type ClipMixer } from "./clipMixer.ts";
import { CLIP_UNAVAILABLE } from "./copy.ts";

/** Recorded lines the page can say as the caller during a browser call. */
export interface CallerClips {
  /** The clip being said right now, or null. */
  sayingUrl: string | null;
  error: string | null;
  say: (clipUrl: string) => void;
}

function openMixer(client: PipecatClient): ClipMixer {
  const microphone = client.tracks().local.audio;
  if (!microphone) {
    throw new Error("the call has no microphone track to mix lines into");
  }
  return createClipMixer(microphone);
}

/** Holds the mixer for one call, from the first line said until the call ends. */
function useCallMixer(client: PipecatClient, onRelease: () => void) {
  const mixer = useRef<ClipMixer | null>(null);

  useEffect(() => {
    const release = () => {
      const current = mixer.current;
      mixer.current = null;
      onRelease();
      void current?.close();
    };
    client.on(RTVIEvent.Disconnected, release);
    return () => {
      client.off(RTVIEvent.Disconnected, release);
      release();
    };
  }, [client, onRelease]);

  return useCallback(() => {
    mixer.current ??= openMixer(client);
    return mixer.current;
  }, [client]);
}

/** Says recorded lines as the caller, mixed with their live microphone, which keeps working. */
export function useCallerClips(client: PipecatClient): CallerClips {
  const [sayingUrl, setSayingUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const handleRelease = useCallback(() => {
    setSayingUrl(null);
    setError(null);
  }, []);
  const mixerForCall = useCallMixer(client, handleRelease);

  const sayClip = useCallback(
    async (clipUrl: string) => {
      setSayingUrl(clipUrl);
      setError(null);
      try {
        const mixer = mixerForCall();
        const clip = await mixer.load(clipUrl);
        if (client.tracks().local.audio !== mixer.track) {
          await sendAsMicrophone(mixer.track);
        }
        await mixer.play(clip);
      } catch {
        setError(CLIP_UNAVAILABLE);
      } finally {
        setSayingUrl((current) => (current === clipUrl ? null : current));
      }
    },
    [client, mixerForCall],
  );

  const say = useCallback(
    (clipUrl: string) => {
      void sayClip(clipUrl);
    },
    [sayClip],
  );
  return useMemo(() => ({ sayingUrl, error, say }), [sayingUrl, error, say]);
}
