import { useEffect, type RefObject } from "react";

const CLEARANCE_PROPERTY = "--sticky-clearance";

/** Publishes where a sticky bar ends once stuck, so a card reached by a link stops below it. */
export function useStickyClearance(bar: RefObject<HTMLElement | null>): void {
  useEffect(() => {
    const element = bar.current;
    if (element === null) {
      return undefined;
    }
    const root = document.documentElement;
    const publish = () => {
      const stuckAt = Number.parseFloat(getComputedStyle(element).top);
      const bottom = (Number.isNaN(stuckAt) ? 0 : stuckAt) + element.offsetHeight;
      root.style.setProperty(CLEARANCE_PROPERTY, `${String(Math.ceil(bottom))}px`);
    };
    publish();
    const observer = new ResizeObserver(publish);
    observer.observe(element);
    window.addEventListener("resize", publish);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", publish);
      root.style.removeProperty(CLEARANCE_PROPERTY);
    };
  }, [bar]);
}
