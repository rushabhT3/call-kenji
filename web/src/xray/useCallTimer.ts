import { useEffect, useState } from "react";

const TICK_MS = 1000;

/** Elapsed call time on this device's clock, so server clock skew never shows. */
export function useCallTimer(startedAtMs: number | null, endedAtMs: number | null): number {
  const [now, setNow] = useState(() => Date.now());
  const isRunning = startedAtMs !== null && endedAtMs === null;

  useEffect(() => {
    if (!isRunning) {
      return undefined;
    }
    const timer = window.setInterval(() => {
      setNow(Date.now());
    }, TICK_MS);
    return () => {
      window.clearInterval(timer);
    };
  }, [isRunning]);

  if (startedAtMs === null) {
    return 0;
  }
  return Math.max(0, (endedAtMs ?? now) - startedAtMs);
}
