import { useEffect, useMemo, useState } from "react";
import type WaveSurfer from "wavesurfer.js";
import type { ReplayClock } from "./clock.ts";
import { SilentClock } from "./silentClock.ts";
import type { Timeline } from "./timeline.ts";
import { createWaveform } from "./waveform.ts";
import { WaveformClock } from "./waveformClock.ts";

interface WaveformLoad {
  clock: ReplayClock | null;
  hasFailed: boolean;
}

export interface Waveform extends WaveformLoad {
  attach: (element: HTMLElement | null) => void;
}

const FAILED: WaveformLoad = { clock: null, hasFailed: true };

/** Reports when the waveform can play, or that it failed; returns the way to tear it down. */
function watchWaveform(waveSurfer: WaveSurfer, onLoad: (load: WaveformLoad) => void): () => void {
  const stopReady = waveSurfer.once("ready", () => {
    onLoad({ clock: new WaveformClock(waveSurfer), hasFailed: false });
  });
  const stopError = waveSurfer.on("error", () => {
    onLoad(FAILED);
  });
  return () => {
    // Unsubscribe first: destroying a waveform that is still loading reports an error.
    stopReady();
    stopError();
    waveSurfer.destroy();
  };
}

/**
 * The recording's sound, drawn as a waveform in the element the player attaches. It becomes a
 * clock once it can play; it fails when the sound cannot be fetched, decoded or played.
 */
export function useWaveformClock(audioUrl: string | null): Waveform {
  const [element, setElement] = useState<HTMLElement | null>(null);
  const [load, setLoad] = useState<WaveformLoad>({ clock: null, hasFailed: false });
  useEffect(() => {
    if (audioUrl === null || element === null) {
      return undefined;
    }
    let tearDown: (() => void) | null = null;
    let isCancelled = false;
    const run = async () => {
      try {
        const waveSurfer = await createWaveform(element, audioUrl);
        tearDown = watchWaveform(waveSurfer, setLoad);
        if (isCancelled) {
          tearDown();
        }
      } catch {
        if (!isCancelled) {
          setLoad(FAILED);
        }
      }
    };
    void run();
    return () => {
      isCancelled = true;
      tearDown?.();
    };
  }, [audioUrl, element]);
  return { ...load, attach: setElement };
}

/** A replay without sound, for fast replays, or when the sound did not load. */
export function useSilentClock(
  timeline: Timeline | null,
  rate: number,
  isAutoplay: boolean,
): SilentClock | null {
  const clock = useMemo(
    () => (timeline ? new SilentClock({ durationMs: timeline.durationMs, rate }) : null),
    [timeline, rate],
  );
  useEffect(() => {
    if (clock === null) {
      return undefined;
    }
    if (isAutoplay) {
      void clock.play();
    }
    return () => {
      clock.pause();
    };
  }, [clock, isAutoplay]);
  return clock;
}
