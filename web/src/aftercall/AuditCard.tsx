import { useState } from "react";
import type { AuditPublished } from "../contract/events.ts";
import { Button } from "../ui/Button.tsx";
import { Pill } from "../ui/Pill.tsx";

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

export function AuditCard({ audit }: { audit: AuditPublished }) {
  const [isExpanded, setIsExpanded] = useState(false);
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
        Every step of the call, each record sealed with the hash of the one before it.
      </p>
      <pre
        className={isExpanded ? "audit__json audit__json--all" : "audit__json"}
        tabIndex={0}
        aria-label="Audit record JSON"
      >
        <code>{json}</code>
      </pre>
      <Button
        variant="quiet"
        size="sm"
        onClick={() => {
          setIsExpanded(!isExpanded);
        }}
      >
        {isExpanded ? "Show less" : "Show all"}
      </Button>
      {state === "failed" ? (
        <p className="audit__error">Select the text and copy it manually.</p>
      ) : null}
      <p className="visually-hidden" aria-live="polite">
        {state === "copied" ? "Audit record copied." : ""}
      </p>
    </section>
  );
}
