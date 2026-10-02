import { useState } from "react";
import type { AuditPublished } from "../contract/events.ts";
import { Button } from "../ui/Button.tsx";
import { Pill } from "../ui/Pill.tsx";
import { formatClock, isoDuration } from "../format.ts";
import { auditTimeline } from "./auditTimeline.ts";

type CopyState = "idle" | "copied" | "failed";
const COPIED_RESET_MS = 2000;

const COPY_LABELS: Record<CopyState, string> = {
  idle: "Copy JSON",
  copied: "Copied",
  failed: "Copy failed",
};

function useCopy(text: string) {
  const [state, setState] = useState<CopyState>("idle");
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setState("copied");
      window.setTimeout(() => {
        setState("idle");
      }, COPIED_RESET_MS);
    } catch {
      setState("failed");
    }
  };
  return { state, copy };
}

interface AuditHeaderProps {
  isChainValid: boolean;
  copyState: CopyState;
  onCopy: () => void;
}

function AuditHeader({ isChainValid, copyState, onCopy }: AuditHeaderProps) {
  return (
    <header className="card__header audit__header">
      <span className="card__marker" aria-hidden="true" />
      <h3 id="audit-title" className="caption card__title">
        Audit record · <span lang="ja">監査記録</span>
      </h3>
      <Pill
        tone={isChainValid ? "pass" : "blocked"}
        label={isChainValid ? "Hash chain verified" : "Chain broken"}
      />
      <Button size="sm" icon={copyState === "copied" ? "check" : "copy"} onClick={onCopy}>
        {COPY_LABELS[copyState]}
      </Button>
    </header>
  );
}

function Timeline({ audit }: { audit: AuditPublished }) {
  return (
    <ol className="audit__timeline" aria-label="Audit record, step by step">
      {auditTimeline(audit).map((entry) => (
        <li key={entry.sequence} className={`audit__entry audit__entry--${entry.tone}`}>
          <time className="caption audit__time" dateTime={isoDuration(entry.offsetMs)}>
            {formatClock(entry.offsetMs)}
          </time>
          <div className="audit__what">
            <p className="audit__title">{entry.title}</p>
            {entry.detail ? <p className="audit__detail">{entry.detail}</p> : null}
          </div>
        </li>
      ))}
    </ol>
  );
}

/** The records as stored, for whoever wants to check the hashes themselves. */
function RawJson({ json }: { json: string }) {
  const [isShown, setIsShown] = useState(false);
  return (
    <>
      <Button
        variant="quiet"
        size="sm"
        aria-expanded={isShown}
        aria-controls="audit-json"
        onClick={() => {
          setIsShown(!isShown);
        }}
      >
        {isShown ? "Hide raw JSON" : "Show raw JSON"}
      </Button>
      {isShown ? (
        <pre id="audit-json" className="audit__json" tabIndex={0} aria-label="Audit record JSON">
          <code>{json}</code>
        </pre>
      ) : null}
    </>
  );
}

export function AuditCard({ audit }: { audit: AuditPublished }) {
  const json = JSON.stringify(audit.records, null, 2);
  const { state, copy } = useCopy(json);
  return (
    <section id="audit" className="card audit" aria-labelledby="audit-title">
      <AuditHeader
        isChainValid={audit.is_chain_valid}
        copyState={state}
        onCopy={() => void copy()}
      />
      <p className="card__summary">
        Every step of the call, in order. Each entry is sealed with the fingerprint of the one
        before it, so changing any entry afterwards would break the chain.
      </p>
      <Timeline audit={audit} />
      <RawJson json={json} />
      {state === "failed" ? (
        <p className="audit__error">Open the raw JSON, select it and copy it by hand.</p>
      ) : null}
      <p className="visually-hidden" aria-live="polite">
        {state === "copied" ? "Audit record copied." : ""}
      </p>
    </section>
  );
}
