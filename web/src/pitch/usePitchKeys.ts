import { useEffect } from "react";
import { firstStepOf, LAST_STEP, OVERVIEW_STEP, STOPS } from "./stops.ts";

export interface PitchMoves {
  next: () => void;
  previous: () => void;
  jump: (step: number) => void;
}

const NEXT_KEYS = new Set(["ArrowRight", "ArrowDown", "PageDown", " "]);
const PREVIOUS_KEYS = new Set(["ArrowLeft", "ArrowUp", "PageUp"]);
/** Keys a focused button or link already answers to; the pitch must not take them over. */
const CONTROL_KEYS = new Set([" ", "Enter"]);

function isTyping(target: EventTarget | null): boolean {
  return target instanceof HTMLElement && target.closest("input, textarea, select") !== null;
}

function isOnControl(target: EventTarget | null): boolean {
  return target instanceof HTMLElement && target.closest("a, button") !== null;
}

function jumpForKey(key: string): number | null {
  if (key === "Home" || key === "0") {
    return OVERVIEW_STEP;
  }
  if (key === "End") {
    return LAST_STEP;
  }
  const stop = /^[1-9]$/.test(key) ? STOPS[Number(key) - 1] : undefined;
  return stop ? firstStepOf(stop.id) : null;
}

/** Runs the move a key asks for; true when the key was the pitch's to take. */
function handlePitchKey(key: string, moves: PitchMoves): boolean {
  if (NEXT_KEYS.has(key)) {
    moves.next();
    return true;
  }
  if (PREVIOUS_KEYS.has(key)) {
    moves.previous();
    return true;
  }
  const step = jumpForKey(key);
  if (step !== null) {
    moves.jump(step);
  }
  return step !== null;
}

/** Arrow keys, Space, Page Up and Down, Home, End and the stop numbers move the camera. */
export function usePitchKeys(isCanvas: boolean, moves: PitchMoves): void {
  useEffect(() => {
    if (!isCanvas) {
      return;
    }
    const handleKey = (event: KeyboardEvent) => {
      const isClaimed = CONTROL_KEYS.has(event.key) && isOnControl(event.target);
      if (event.altKey || event.ctrlKey || event.metaKey || isClaimed || isTyping(event.target)) {
        return;
      }
      if (handlePitchKey(event.key, moves)) {
        event.preventDefault();
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => {
      window.removeEventListener("keydown", handleKey);
    };
  }, [isCanvas, moves]);
}
