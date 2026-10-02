import { outcomeLabel } from "../call/copy.ts";
import type { CallOutcome } from "../contract/events.ts";
import { formatCount } from "../format.ts";
import type { PromiseFacts } from "./promise.ts";

interface OutcomeCardProps {
  outcome: CallOutcome;
  promise: PromiseFacts | null;
}

function PromiseFactsRow({ promise }: { promise: PromiseFacts }) {
  return (
    <dl className="outcome__facts">
      <div>
        <dt className="caption">Monthly · 毎月</dt>
        <dd className="outcome__metric numeric">¥{formatCount(promise.monthlyYen)}</dd>
      </div>
      <div>
        <dt className="caption">Payments · 回数</dt>
        <dd className="outcome__fact numeric">{promise.installments}</dd>
      </div>
      <div>
        <dt className="caption">First payment · 初回</dt>
        <dd className="outcome__fact numeric">{promise.firstPaymentOn}</dd>
      </div>
    </dl>
  );
}

export function OutcomeCard({ outcome, promise }: OutcomeCardProps) {
  const label = outcomeLabel(outcome);
  return (
    <section className="outcome" aria-labelledby="outcome-title">
      <p className="caption outcome__caption">
        Outcome · <span lang="ja">結果</span>
      </p>
      <h3 id="outcome-title" className="outcome__title">
        {label.en}
        <span className="outcome__ja" lang="ja">
          {label.ja}
        </span>
      </h3>
      {promise ? <PromiseFactsRow promise={promise} /> : null}
    </section>
  );
}
