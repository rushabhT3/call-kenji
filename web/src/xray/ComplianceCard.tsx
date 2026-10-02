import { COMPLIANCE_CHECKS, complianceSummary } from "../call/copy.ts";
import type { ComplianceUpdated } from "../contract/events.ts";
import { Card } from "../ui/Card.tsx";
import { Pill } from "../ui/Pill.tsx";

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
        {COMPLIANCE_CHECKS.map(({ key, label, blockedReason }) => {
          const status = compliance?.[key] ?? "pending";
          return (
            <li key={key} className="check">
              <span className="check__label">
                {label.en}
                <span className="caption" lang="ja">
                  {label.ja}
                </span>
              </span>
              <Pill tone={status} context={label.en} />
              {status === "blocked" && blockedReason ? (
                <p className="check__reason">{blockedReason}</p>
              ) : null}
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
