import type { CheckStatus, StrategistUpdated } from "../contract/events.ts";
import { Card, Row } from "../ui/Card.tsx";
import { Pill } from "../ui/Pill.tsx";

const IDENTITY_LABELS: Record<CheckStatus, string> = {
  pass: "Verified",
  pending: "Unverified",
  blocked: "Locked",
};

interface StrategistCardProps {
  advice: StrategistUpdated | null;
  identityGate: CheckStatus | null;
}

function Offers({ offers }: { offers: readonly string[] }) {
  if (offers.length === 0) {
    return <span>None yet</span>;
  }
  return (
    <ul className="offers">
      {offers.map((offer) => (
        <li key={offer} className="numeric">
          {offer}
        </li>
      ))}
    </ul>
  );
}

export function StrategistCard({ advice, identityGate }: StrategistCardProps) {
  if (advice === null) {
    return (
      <Card
        id="strategist"
        title="Strategist"
        titleJa="戦略"
        summary="Waiting for your first turn. A second model then reads each turn and advises Kenji."
        isEmpty
      />
    );
  }
  const identity = identityGate ?? "pending";
  return (
    <Card
      id="strategist"
      title="Strategist"
      titleJa="戦略"
      summary={`Next move: ${advice.next_move}`}
    >
      <dl className="rows">
        <Row label="Identity" labelJa="本人確認">
          <Pill tone={identity} label={IDENTITY_LABELS[identity]} context="Identity" />
        </Row>
        <Row isStacked label="Situation" labelJa="状況">
          {advice.situation}
        </Row>
        <Row isStacked label="Ability to pay" labelJa="支払い能力">
          {advice.ability_to_pay}
        </Row>
        <Row isStacked label="Offers" labelJa="提案">
          <Offers offers={advice.offers} />
        </Row>
      </dl>
    </Card>
  );
}
