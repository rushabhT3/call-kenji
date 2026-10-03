import { useCallback, useEffect, useMemo, useRef, useState, type RefObject } from "react";

/** Waiting for the first play, playing (or played), or the file could not be loaded. */
export type TrailerStatus = "ready" | "playing" | "failed";

export interface TrailerState {
  status: TrailerStatus;
  /** The browser turned down a press of Play; its own controls may still start the video. */
  isPlayRefused: boolean;
  /** Changes on every retry, so the player can be rebuilt and fetch the file again. */
  attempt: number;
}

export interface TrailerActions {
  play: () => Promise<void>;
  markPlaying: () => void;
  markFailed: () => void;
  retry: () => void;
}

export interface TrailerVideo {
  videoRef: RefObject<HTMLVideoElement | null>;
  state: TrailerState;
  actions: TrailerActions;
}

type PlaybackStart = "started" | "failed" | "refused";

async function startPlayback(video: HTMLVideoElement): Promise<PlaybackStart> {
  try {
    await video.play();
    video.focus();
    return "started";
  } catch {
    return video.error ? "failed" : "refused";
  }
}

// React sets the source before the player is attached, so a quick failure can come and go before
// its error listener is live; whatever the player already knows is read once it is on the page.
function useEarlyFailure(
  videoRef: RefObject<HTMLVideoElement | null>,
  attempt: number,
  onFailure: () => void,
): void {
  useEffect(() => {
    if (videoRef.current?.error) {
      onFailure();
    }
  }, [videoRef, attempt, onFailure]);
}

export function useTrailerVideo(): TrailerVideo {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [status, setStatus] = useState<TrailerStatus>("ready");
  const [isPlayRefused, setIsPlayRefused] = useState(false);
  const [attempt, setAttempt] = useState(0);

  const markPlaying = useCallback(() => {
    setIsPlayRefused(false);
    setStatus("playing");
  }, []);
  const markFailed = useCallback(() => {
    setStatus("failed");
  }, []);
  const retry = useCallback(() => {
    setAttempt((previous) => previous + 1);
    setIsPlayRefused(false);
    setStatus("ready");
  }, []);
  const play = useCallback(async () => {
    const video = videoRef.current;
    const start = video ? await startPlayback(video) : "started";
    if (start === "failed") {
      setStatus("failed");
    }
    setIsPlayRefused(start === "refused");
  }, []);
  useEarlyFailure(videoRef, attempt, markFailed);

  const actions = useMemo(
    () => ({ play, markPlaying, markFailed, retry }),
    [play, markPlaying, markFailed, retry],
  );
  return { videoRef, state: { status, isPlayRefused, attempt }, actions };
}
