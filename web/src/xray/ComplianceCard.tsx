import { COMPLIANCE_CHECKS, complianceSummary } from "../call/copy.ts";
import type { CheckStatus, ComplianceUpdated } from "../contract/events.ts";
import { Card } from "../ui/Card.tsx";
import { Pill } from "../ui/Pill.tsx";

interface CheckProps {
  check: (typeof COMPLIANCE_CHECKS)[number];
  status: CheckStatus;
  note: string | undefined;
}

function Check({ check: { label, blockedReason }, status, note }: CheckProps) {
  return (
    <li className="check">
      <span className="check__label">
        {label.en}
        <span className="caption" lang="ja">
          {label.ja}
        </span>
      </span>
      <Pill tone={status} context={label.en} />
      {note ? <p className="check__note">{note}</p> : null}
      {status === "blocked" && blockedReason ? (
        <p className="check__reason">{blockedReason}</p>
      ) : null}
    </li>
  );
}

export function ComplianceCard({ compliance }: { compliance: ComplianceUpdated | null }) {
  return (
    <Card
      id="compliance"
      title="Compliance"
      titleJa="コンプライアンス"
      summary={complianceSummary(compliance)}
      isEmpty={compliance === null}
    >
      <ul className="checks">
        {COMPLIANCE_CHECKS.map((check) => (
          <Check
            key={check.key}
            check={check}
            status={compliance?.[check.key] ?? "pending"}
            note={check.key === "calling_hours" ? compliance?.calling_hours_note : undefined}
          />
        ))}
      </ul>
    </Card>
  );
}
