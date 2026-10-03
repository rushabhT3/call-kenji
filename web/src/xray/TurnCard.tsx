import { nodeLabel, turnEndSentence } from "../call/copy.ts";
import type { TurnAssessed, TurnEndJudged } from "../contract/events.ts";
import { formatCount, formatScore } from "../format.ts";
import { BudgetBar } from "../ui/BudgetBar.tsx";
import { Card, Row } from "../ui/Card.tsx";
import { Pill } from "../ui/Pill.tsx";

interface TurnCardProps {
  turn: TurnAssessed | null;
  turnEnd: TurnEndJudged | null;
}

function summary(turn: TurnAssessed): string {
  const said = `You said 「${turn.utterance}」 while Kenji was talking.`;
  return turn.verdict === "backchannel"
    ? `${said} He kept going: that was aizuchi, not an interruption.`
    : `${said} He stopped to listen: that was a real interruption.`;
}

function Measures({ turn }: { turn: TurnAssessed }) {
  const measures = [
    { label: "Last overlap", ja: "重なり", value: `${formatCount(turn.overlap_ms)} ms` },
    { label: "Characters", ja: "文字数", value: String(turn.characters) },
    { label: "Score", ja: "スコア", value: formatScore(turn.score) },
  ];
  return (
    <dl className="measures">
      {measures.map((measure) => (
        <div key={measure.label} className="measures__item">
          <dt className="caption">
            {measure.label} <span lang="ja">{measure.ja}</span>
          </dt>
          <dd className="metric-sm">{measure.value}</dd>
        </div>
      ))}
    </dl>
  );
}

function VerdictPill({ turn }: { turn: TurnAssessed }) {
  const isBackchannel = turn.verdict === "backchannel";
  return (
    <Pill
      tone={isBackchannel ? "info" : "caution"}
      label={isBackchannel ? "Backchannel" : "Interruption"}
    />
  );
}

function OverlapCard({ turn, turnEnd }: { turn: TurnAssessed; turnEnd: TurnEndJudged | null }) {
  const node = nodeLabel(turn.node);
  return (
    <Card
      id="turn"
      title="Turn"
      titleJa="ターン"
      summary={summary(turn)}
      status={<VerdictPill turn={turn} />}
    >
      <BudgetBar
        value={turn.score}
        scale={1}
        marker={turn.threshold}
        markerLabel={`Interrupts at ${formatScore(turn.threshold)}`}
        fill="ink"
        label="Interruption score"
      />
      <Measures turn={turn} />
      <dl className="rows">
        <Row label="Flow step" labelJa="ステップ">
          {node.en} <code className="caption code-id">{turn.node}</code>
        </Row>
        {turnEnd ? (
          <Row label="End of your turn" labelJa="話し終わり" isStacked>
            {turnEndSentence(turnEnd)}
          </Row>
        ) : null}
      </dl>
    </Card>
  );
}

export function TurnCard({ turn, turnEnd }: TurnCardProps) {
  if (turn !== null) {
    return <OverlapCard turn={turn} turnEnd={turnEnd} />;
  }
  if (turnEnd !== null) {
    return <Card id="turn" title="Turn" titleJa="ターン" summary={turnEndSentence(turnEnd)} />;
  }
  return (
    <Card
      id="turn"
      title="Turn"
      titleJa="ターン"
      summary="Nothing yet. Speak, or talk over Kenji, and this card shows how he decides."
      isEmpty
    />
  );
}
