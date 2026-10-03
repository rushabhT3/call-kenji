import { useCallback, useEffect, useState } from "react";
import { nextPosition, previousPosition, startOf, type Position } from "./position.ts";
import { OVERVIEW_STEP, stepFromHash } from "./stops.ts";

export interface PitchPosition {
  position: Position;
  next: () => void;
  previous: () => void;
  jump: (step: number) => void;
}

function writeHash(step: number): void {
  const { pathname, search } = window.location;
  const hash = step === OVERVIEW_STEP ? "" : `#${String(step)}`;
  window.history.replaceState(null, "", `${pathname}${search}${hash}`);
}

/** Where the reader is, with the step kept in the address as "#3" so a link can open there. */
export function usePitchPosition(pageCounts: readonly number[]): PitchPosition {
  const [position, setPosition] = useState(() => startOf(stepFromHash(window.location.hash)));

  useEffect(() => {
    writeHash(position.step);
  }, [position.step]);

  useEffect(() => {
    const followAddress = () => {
      setPosition(startOf(stepFromHash(window.location.hash)));
    };
    window.addEventListener("hashchange", followAddress);
    return () => {
      window.removeEventListener("hashchange", followAddress);
    };
  }, []);

  const next = useCallback(() => {
    setPosition((current) => nextPosition(current, pageCounts));
  }, [pageCounts]);
  const previous = useCallback(() => {
    setPosition((current) => previousPosition(current, pageCounts));
  }, [pageCounts]);
  const jump = useCallback((step: number) => {
    setPosition(startOf(step));
  }, []);

  return { position, next, previous, jump };
}
