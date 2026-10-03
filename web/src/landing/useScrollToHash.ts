import { useEffect } from "react";

/**
 * A link from another page to a section here lands on it once everything above it is drawn: on a
 * phone the persona card sits above the call panel and only takes its height when the catalog loads.
 */
export function useScrollToHash(isLaidOut: boolean): void {
  useEffect(() => {
    const id = decodeURIComponent(window.location.hash.slice(1));
    if (isLaidOut && id) {
      document.getElementById(id)?.scrollIntoView();
    }
  }, [isLaidOut]);
}
