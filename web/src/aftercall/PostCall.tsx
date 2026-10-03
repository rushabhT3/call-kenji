import { useEffect, useRef } from "react";
import type { CallView } from "../call/callView.ts";
import { AuditCard } from "./AuditCard.tsx";
import { HandoffCard } from "./HandoffCard.tsx";
import { NextCall } from "./NextCall.tsx";
import { OutcomeCard } from "./OutcomeCard.tsx";
import { promiseFromAudit } from "./promise.ts";
import { SmsCard } from "./SmsCard.tsx";

interface PostCallProps {
  view: CallView;
  isDemo: boolean;
}

export function PostCall({ view, isDemo }: PostCallProps) {
  const headingRef = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    if (!isDemo) {
      headingRef.current?.focus();
    }
  }, [isDemo]);
  if (view.outcome === null) {
    return null;
  }
  return (
    <section className="post-call" aria-labelledby="post-call-title">
      <h2 id="post-call-title" ref={headingRef} tabIndex={-1} className="post-call__title">
        What happened · <span lang="ja">通話の結果</span>
      </h2>
      <OutcomeCard outcome={view.outcome} promise={promiseFromAudit(view.audit)} />
      <NextCall isDemo={isDemo} />
      <div className="post-call__pair">
        <SmsCard sms={view.sms} />
        <HandoffCard handoff={view.handoff} />
      </div>
      {view.audit ? <AuditCard audit={view.audit} /> : null}
    </section>
  );
}
