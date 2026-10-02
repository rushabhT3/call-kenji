import type { CallView } from "../call/callView.ts";
import { nowSentence } from "../call/copy.ts";

export function NowStrip({ view }: { view: CallView }) {
  const sentence = nowSentence(view.status, view.node);
  return (
    <section className="now" aria-labelledby="now-title" aria-live="polite">
      <h2 id="now-title" className="caption">
        Now · <span lang="ja">いま</span>
      </h2>
      <p key={sentence.en} className="now__sentence">
        {sentence.en}
      </p>
      <p className="now__ja" lang="ja">
        {sentence.ja}
      </p>
    </section>
  );
}
