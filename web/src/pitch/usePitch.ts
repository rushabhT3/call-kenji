import { useCallback, useMemo, useState } from "react";
import { isAtEnd, type Position } from "./position.ts";
import { useAutoplay } from "./useAutoplay.ts";
import { useCamera, type CameraRefs } from "./useCamera.ts";
import { useFrames } from "./useFrames.ts";
import { useMotionAllowed } from "./useMotionAllowed.ts";
import { usePitchKeys, type PitchMoves } from "./usePitchKeys.ts";
import { usePitchPosition } from "./usePitchPosition.ts";

export interface Pitch {
  isCanvas: boolean;
  position: Position;
  pageCounts: readonly number[];
  isPlaying: boolean;
  togglePlay: () => void;
  /** Moves the reader asked for, which also stop autoplay. */
  moves: PitchMoves;
}

/** The reader's own moves: each one also stops autoplay, so a hand on the controls wins. */
function useReaderMoves(moves: PitchMoves, stop: () => void): PitchMoves {
  const { next, previous, jump } = moves;
  return useMemo<PitchMoves>(
    () => ({
      next: () => {
        stop();
        next();
      },
      previous: () => {
        stop();
        previous();
      },
      jump: (step) => {
        stop();
        jump(step);
      },
    }),
    [next, previous, jump, stop],
  );
}

/** Everything the pitch page runs on: the layout's pages, where the reader is, and how they move. */
export function usePitch(refs: CameraRefs): Pitch {
  const isCanvas = useMotionAllowed();
  const frames = useFrames(refs, isCanvas);
  const pageCounts = useMemo(() => frames?.map((pages) => pages.length) ?? [], [frames]);
  const { position, next, previous, jump } = usePitchPosition(pageCounts);
  const [isPlaying, setPlaying] = useState(false);
  const stop = useCallback(() => {
    setPlaying(false);
  }, []);
  const moves = useReaderMoves({ next, previous, jump }, stop);
  const key = `${String(position.step)}.${String(position.page)}`;
  useCamera(refs, { frame: frames?.[position.step]?.[position.page] ?? null, key }, isCanvas);
  usePitchKeys(isCanvas, moves);
  useAutoplay({
    isPlaying,
    positionKey: key,
    isAtEnd: isAtEnd(position, pageCounts),
    advance: next,
    stop,
  });
  const togglePlay = useCallback(() => {
    setPlaying((playing) => !playing);
  }, []);
  return { isCanvas, position, pageCounts, isPlaying, togglePlay, moves };
}
