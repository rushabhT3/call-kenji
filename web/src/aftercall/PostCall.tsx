import { useEffect, useRef } from "react";
import type { CallView } from "../call/callView.ts";
import { AuditCard } from "./AuditCard.tsx";
import { HandoffCard } from "./HandoffCard.tsx";
import { OutcomeCard } from "./OutcomeCard.tsx";
import { promiseFromAudit } from "./promise.ts";
import { SmsCard } from "./SmsCard.tsx";

export function PostCall({ view }: { view: CallView }) {
  const headingRef = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    headingRef.current?.focus();
  }, []);
  if (view.outcome === null) {
    return null;
  }
  return (
    <section className="post-call" aria-labelledby="post-call-title">
      <h2 id="post-call-title" ref={headingRef} tabIndex={-1} className="post-call__title">
        What happened · <span lang="ja">通話の結果</span>
      </h2>
      <OutcomeCard outcome={view.outcome} promise={promiseFromAudit(view.audit)} />
      <div className="post-call__pair">
        <SmsCard sms={view.sms} />
        <HandoffCard handoff={view.handoff} />
      </div>
      {view.audit ? <AuditCard audit={view.audit} /> : null}
    </section>
  );
}
