import { useGSAP } from "@gsap/react";
import { gsap } from "gsap";
import { DrawSVGPlugin } from "gsap/DrawSVGPlugin";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { SplitText } from "gsap/SplitText";
import type { RefObject } from "react";
import { animateShowcase } from "./motion.ts";

gsap.registerPlugin(useGSAP, ScrollTrigger, SplitText, DrawSVGPlugin);

const WIDE_WITH_MOTION = "(min-width: 1024px) and (prefers-reduced-motion: no-preference)";
const NARROW_WITH_MOTION = "(max-width: 1023px) and (prefers-reduced-motion: no-preference)";

// Lines and pin distances are measured with the fallback font until the display fonts land.
async function refreshOnceFontsLoad(): Promise<void> {
  await document.fonts.ready;
  ScrollTrigger.refresh();
}

/** Scroll animation for the features page, only for readers who have not asked for less motion. */
export function useShowcaseMotion(scope: RefObject<HTMLElement | null>): void {
  useGSAP(
    () => {
      const root = scope.current;
      if (!root) {
        return;
      }
      const media = gsap.matchMedia(root);
      media.add(WIDE_WITH_MOTION, () => animateShowcase(root, { isPinned: true }));
      media.add(NARROW_WITH_MOTION, () => animateShowcase(root, { isPinned: false }));
      void refreshOnceFontsLoad();
      return () => {
        media.revert();
      };
    },
    { scope },
  );
}
