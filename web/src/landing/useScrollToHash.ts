import { useEffect } from "react";

/** A link from another page to a section here lands on it once the page has rendered. */
export function useScrollToHash(): void {
  useEffect(() => {
    const id = decodeURIComponent(window.location.hash.slice(1));
    if (id) {
      document.getElementById(id)?.scrollIntoView();
    }
  }, []);
}
