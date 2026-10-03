import { LAST_STEP, OVERVIEW_STEP } from "./stops.ts";

/** Where the camera is: a step of the story, and a page within it when the step is tall. */
export interface Position {
  step: number;
  page: number;
}

export function startOf(step: number): Position {
  return { step: Math.min(Math.max(step, OVERVIEW_STEP), LAST_STEP), page: 0 };
}

function pagesAt(step: number, pageCounts: readonly number[]): number {
  return Math.max(pageCounts[step] ?? 1, 1);
}

/** On down the page first, then on to the next step. */
export function nextPosition(position: Position, pageCounts: readonly number[]): Position {
  if (position.page + 1 < pagesAt(position.step, pageCounts)) {
    return { step: position.step, page: position.page + 1 };
  }
  return position.step < LAST_STEP ? startOf(position.step + 1) : position;
}

/** Back up the page first, then to the bottom of the step before. */
export function previousPosition(position: Position, pageCounts: readonly number[]): Position {
  if (position.page > 0) {
    return { step: position.step, page: position.page - 1 };
  }
  if (position.step <= OVERVIEW_STEP) {
    return position;
  }
  const step = position.step - 1;
  return { step, page: pagesAt(step, pageCounts) - 1 };
}

export function isAtEnd(position: Position, pageCounts: readonly number[]): boolean {
  return nextPosition(position, pageCounts) === position;
}
