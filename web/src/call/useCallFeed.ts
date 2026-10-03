import { useCallback, useEffect, useReducer, useState } from "react";
import type { CallEvent } from "../contract/events.ts";
import { useReplay, type ReplayPlayer } from "../demo/useReplay.ts";
import { EMPTY_CALL, applyEvent, type CallView } from "./callView.ts";
import { openViewerFeed, viewerSocketUrl, type FeedStatus } from "./viewerFeed.ts";

export interface CallFeed {
  view: CallView;
  feedStatus: FeedStatus;
  viewerId: string | null;
  code: string | null;
  /** The demo's recorded call, to play and to move through; null on a live call. */
  replay: ReplayPlayer | null;
  /**
   * When the call started and ended on this device's clock. A replay's clock stands at the
   * playhead: it starts at 0 and has run as far as the replay has got.
   */
  startedAtMs: number | null;
  endedAtMs: number | null;
}

interface FeedOptions {
  isDemo: boolean;
  speed: number;
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

function useLiveCall(isEnabled: boolean) {
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
  const feed = useLiveFeed(isEnabled, dispatch);
  return { view, clock, feed };
}

export function useCallFeed({ isDemo, speed }: FeedOptions): CallFeed {
  const live = useLiveCall(!isDemo);
  const replay = useReplay(isDemo, speed);
  if (replay) {
    return {
      view: replay.view,
      feedStatus: "open",
      viewerId: null,
      code: null,
      replay: replay.player,
      startedAtMs: 0,
      endedAtMs: replay.player.positionMs,
    };
  }
  return {
    view: live.view,
    feedStatus: live.feed.status,
    viewerId: live.feed.link?.viewerId ?? null,
    code: live.feed.link?.code ?? null,
    replay: null,
    startedAtMs: live.clock.startedAtMs,
    endedAtMs: live.clock.endedAtMs,
  };
}
