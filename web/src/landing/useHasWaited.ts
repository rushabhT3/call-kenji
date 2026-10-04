import { useEffect, useState } from "react";

/** True once something has been waited on for longer than the delay, so quick waits stay quiet. */
export function useHasWaited(isWaiting: boolean, delayMs: number): boolean {
  const [hasWaited, setHasWaited] = useState(false);
  useEffect(() => {
    if (!isWaiting) {
      return;
    }
    const timer = window.setTimeout(() => {
      setHasWaited(true);
    }, delayMs);
    return () => {
      window.clearTimeout(timer);
    };
  }, [isWaiting, delayMs]);
  return isWaiting && hasWaited;
}
