import { useRef, useState } from "react";
import type { CallView } from "../call/callView.ts";
import { ON_HOLD, nowSentence } from "../call/copy.ts";
import { useStickyClearance } from "./useStickyClearance.ts";

interface NowStripProps {
  view: CallView;
  /** The caller pressed Hold: the strip says Kenji is waiting for them. */
  isOnHold: boolean;
}

export function NowStrip({ view, isOnHold }: NowStripProps) {
  const [isJapaneseShown, setIsJapaneseShown] = useState(false);
  const sentence = isOnHold ? ON_HOLD : nowSentence(view.status, view.node);
  const strip = useRef<HTMLElement>(null);
  useStickyClearance(strip);
  return (
    <section ref={strip} className="now" aria-labelledby="now-title" aria-live="polite">
      <div className="now__head">
        <h2 id="now-title" className="caption">
          Now · <span lang="ja">いま</span>
        </h2>
        <button
          type="button"
          className="caption now__toggle"
          aria-expanded={isJapaneseShown}
          aria-controls="now-ja"
          onClick={() => {
            setIsJapaneseShown(!isJapaneseShown);
          }}
        >
          <span lang="ja">日本語</span>
        </button>
      </div>
      <p key={sentence.en} className="now__sentence">
        {sentence.en}
      </p>
      <p id="now-ja" className={isJapaneseShown ? "now__ja now__ja--shown" : "now__ja"} lang="ja">
        {sentence.ja}
      </p>
    </section>
  );
}
