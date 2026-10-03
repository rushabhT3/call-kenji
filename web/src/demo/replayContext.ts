import { createContext, use } from "react";
import type { ReplayPlayer } from "./useReplay.ts";

/** The demo's player, for the parts of the X-ray that control it; null on a live call. */
export const ReplayContext = createContext<ReplayPlayer | null>(null);

export function useReplayPlayer(): ReplayPlayer | null {
  return use(ReplayContext);
}

/** Plays the recorded call from a line of its transcript; null on a live call. */
export function useLinePlayer(): ((lineId: string) => void) | null {
  return use(ReplayContext)?.playLine ?? null;
}
