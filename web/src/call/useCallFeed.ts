import { useCallback, useEffect, useReducer, useState } from "react";
import type { CallEvent } from "../contract/events.ts";
import { EMPTY_CALL, applyEvent, type CallView } from "./callView.ts";
import { loadRecording, recordingAudioUrl, replaySchedule, startReplay } from "./demoReplay.ts";
import { openViewerFeed, viewerSocketUrl, type FeedStatus } from "./viewerFeed.ts";

/** The replay's audio and when the replay began, so sound can join it at the right moment. */
export interface DemoAudio {
  url: string;
  startedAtMs: number;
}

export interface CallFeed {
  view: CallView;
  feedStatus: FeedStatus;
  viewerId: string | null;
  code: string | null;
  replayError: string | null;
  demoAudio: DemoAudio | null;
  startedAtMs: number | null;
  endedAtMs: number | null;
}

interface FeedOptions {
  isDemo: boolean;
  speed: number;
}

function useDemoFeed(isEnabled: boolean, speed: number, dispatch: (event: CallEvent) => void) {
  const [error, setError] = useState<string | null>(null);
  const [audio, setAudio] = useState<DemoAudio | null>(null);
  useEffect(() => {
    if (!isEnabled) {
      return undefined;
    }
    let stop: (() => void) | undefined;
    let isCancelled = false;
    const run = async () => {
      try {
        const recording = await loadRecording();
        if (isCancelled) {
          return;
        }
        stop = startReplay(replaySchedule(recording, speed), dispatch);
        const url = recordingAudioUrl(recording, speed);
        setAudio(url ? { url, startedAtMs: Date.now() } : null);
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : String(cause));
      }
    };
    void run();
    return () => {
      isCancelled = true;
      stop?.();
    };
  }, [isEnabled, speed, dispatch]);
  return { error, audio };
}

function useLiveFeed(isEnabled: boolean, dispatch: (event: CallEvent) => void) {
  const [status, setStatus] = useState<FeedStatus>("connecting");
  const [link, setLink] = useState<{ viewerId: string; code: string } | null>(null);
  useEffect(() => {
    if (!isEnabled) {
      return undefined;
    }
    return openViewerFeed(viewerSocketUrl(window.location), {
      onReady: (viewerId, code) => {
        setLink({ viewerId, code });
      },
      onEvent: dispatch,
      onStatus: setStatus,
    });
  }, [isEnabled, dispatch]);
  return { status, link };
}

function useLocalCallClock() {
  const [startedAtMs, setStartedAtMs] = useState<number | null>(null);
  const [endedAtMs, setEndedAtMs] = useState<number | null>(null);
  const note = useCallback((event: CallEvent) => {
    if (event.type === "call_started") {
      setStartedAtMs(Date.now());
    } else if (event.type === "call_ended") {
      setEndedAtMs(Date.now());
    }
  }, []);
  return { startedAtMs, endedAtMs, note };
}

export function useCallFeed({ isDemo, speed }: FeedOptions): CallFeed {
  const [view, apply] = useReducer(applyEvent, EMPTY_CALL);
  const clock = useLocalCallClock();
  const { note } = clock;
  const dispatch = useCallback(
    (event: CallEvent) => {
      note(event);
      apply(event);
    },
    [note],
  );
  const replay = useDemoFeed(isDemo, speed, dispatch);
  const live = useLiveFeed(!isDemo, dispatch);
  return {
    view,
    feedStatus: isDemo ? "open" : live.status,
    viewerId: live.link?.viewerId ?? null,
    code: live.link?.code ?? null,
    replayError: replay.error,
    demoAudio: replay.audio,
    startedAtMs: clock.startedAtMs,
    endedAtMs: clock.endedAtMs,
  };
}
