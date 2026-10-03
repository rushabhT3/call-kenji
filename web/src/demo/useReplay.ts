import { useCallback, useMemo, useState, useSyncExternalStore } from "react";
import type { CallView } from "../call/callView.ts";
import type { ReplayClock } from "./clock.ts";
import { settledPosition } from "./playhead.ts";
import { speakerRegions, type SpeakerRegion } from "./speakerRegions.ts";
import { eventsHappenedBy, lineCueMs, viewAfter, type Timeline } from "./timeline.ts";
import { useRecording, type RecordingLoad } from "./useRecording.ts";
import { useSilentClock, useWaveformClock, type Waveform } from "./useReplayClocks.ts";

/** The recording's sound: none by design (a fast replay), loading, in step, or lost. */
export type SoundState = "off" | "loading" | "on" | "failed";

export interface ReplayPlayer {
  recording: RecordingLoad["status"];
  sound: SoundState;
  /** How fast the replay runs: 1 with sound, faster for a quick replay without it. */
  rate: number;
  positionMs: number;
  durationMs: number;
  isPlaying: boolean;
  /** The browser would not start the sound on the last press of Play. */
  isPlayRefused: boolean;
  regions: readonly SpeakerRegion[];
  togglePlay: () => void;
  seek: (positionMs: number) => void;
  /** Plays the call from just before a line of its transcript. */
  playLine: (lineId: string) => void;
  /** Takes the element the waveform is drawn in, once the recording has sound. */
  attachWaveform: (element: HTMLElement | null) => void;
}

export interface Replay {
  view: CallView;
  player: ReplayPlayer;
}

interface Controls {
  isPlayRefused: boolean;
  togglePlay: () => void;
  seek: (positionMs: number) => void;
  playLine: (lineId: string) => void;
}

const EMPTY_TIMELINE: Timeline = { events: [], durationMs: 0 };
const NOTHING_TO_STOP = () => undefined;

function soundState(audioUrl: string | null, waveform: Waveform): SoundState {
  if (audioUrl === null) {
    return "off";
  }
  if (waveform.hasFailed) {
    return "failed";
  }
  return waveform.clock ? "on" : "loading";
}

function isInterruption(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

/** Where the clock is, settled to the moments the screen changes, and whether it is moving. */
function usePlayhead(clock: ReplayClock | null, timeline: Timeline) {
  const subscribe = useCallback(
    (onChange: () => void) => (clock ? clock.subscribe(onChange) : NOTHING_TO_STOP),
    [clock],
  );
  const positionMs = useSyncExternalStore(subscribe, () =>
    clock ? settledPosition(timeline, clock.positionMs()) : 0,
  );
  const isPlaying = useSyncExternalStore(subscribe, () => clock?.isPlaying() ?? false);
  return { positionMs, isPlaying };
}

function useControls(clock: ReplayClock | null, timeline: Timeline): Controls {
  const [isPlayRefused, setIsPlayRefused] = useState(false);
  const play = useCallback(async (from: ReplayClock) => {
    try {
      await from.play();
      setIsPlayRefused(false);
    } catch (error) {
      setIsPlayRefused(!isInterruption(error));
    }
  }, []);
  const togglePlay = useCallback(() => {
    if (clock?.isPlaying()) {
      clock.pause();
    } else if (clock) {
      void play(clock);
    }
  }, [clock, play]);
  const seek = useCallback(
    (positionMs: number) => {
      clock?.seek(positionMs);
    },
    [clock],
  );
  const playLine = useCallback(
    (lineId: string) => {
      const cueMs = lineCueMs(timeline, lineId);
      if (clock && cueMs !== null) {
        clock.seek(cueMs);
        void play(clock);
      }
    },
    [clock, timeline, play],
  );
  return { isPlayRefused, togglePlay, seek, playLine };
}

/**
 * The demo's recorded call as a player. The X-ray is whatever the call's events made of it by
 * the playhead, so seeking anywhere is one pure step. With sound, the playhead is the audio's
 * own position; without it, the page's clock at the requested speed. Null on a live call.
 */
export function useReplay(isEnabled: boolean, speed: number): Replay | null {
  const load = useRecording(isEnabled, speed);
  const timeline = load.status === "ready" ? load.timeline : null;
  const audioUrl = load.status === "ready" ? load.audioUrl : null;
  const waveform = useWaveformClock(audioUrl);
  const silent = useSilentClock(timeline, speed, audioUrl === null);
  const sound = soundState(audioUrl, waveform);
  const clock = sound === "on" ? waveform.clock : sound === "loading" ? null : silent;
  const shown = timeline ?? EMPTY_TIMELINE;
  const playhead = usePlayhead(clock, shown);
  const controls = useControls(clock, shown);
  const count = eventsHappenedBy(shown, playhead.positionMs);
  const view = useMemo(() => viewAfter(shown, count), [shown, count]);
  const regions = useMemo(() => speakerRegions(shown), [shown]);
  if (!isEnabled) {
    return null;
  }
  const player: ReplayPlayer = {
    ...controls,
    ...playhead,
    recording: load.status,
    sound,
    rate: speed,
    durationMs: clock?.durationMs ?? shown.durationMs,
    regions,
    attachWaveform: waveform.attach,
  };
  return { view, player };
}
