import { useEffect } from "react";

/** Long enough to read a page's headline and glance at its picture before the camera moves. */
const SECONDS_PER_PAGE = 6;
const MILLISECONDS_PER_SECOND = 1000;

interface Autoplay {
  isPlaying: boolean;
  /** Changes on every move, so each page gets its full time on screen. */
  positionKey: string;
  isAtEnd: boolean;
  advance: () => void;
  stop: () => void;
}

/** Plays the pitch like a film, a page at a time, and stops at the end. */
export function useAutoplay({ isPlaying, positionKey, isAtEnd, advance, stop }: Autoplay): void {
  useEffect(() => {
    if (!isPlaying) {
      return;
    }
    if (isAtEnd) {
      stop();
      return;
    }
    const timer = window.setTimeout(advance, SECONDS_PER_PAGE * MILLISECONDS_PER_SECOND);
    return () => {
      window.clearTimeout(timer);
    };
  }, [isPlaying, positionKey, isAtEnd, advance, stop]);
}
