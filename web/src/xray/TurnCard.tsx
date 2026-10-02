import { nodeLabel } from "../call/copy.ts";
import type { TurnAssessed } from "../contract/events.ts";
import { formatCount, formatScore } from "../format.ts";
import { BudgetBar } from "../ui/BudgetBar.tsx";
import { Card, Row } from "../ui/Card.tsx";
import { Pill } from "../ui/Pill.tsx";

function summary(turn: TurnAssessed): string {
  const said = `You said 「${turn.utterance}」 while Kenji was talking.`;
  return turn.verdict === "backchannel"
    ? `${said} He kept going, because that was aizuchi, not an interruption.`
    : `${said} He stopped to listen, because that was a real interruption.`;
}

function Details({ turn }: { turn: TurnAssessed }) {
  const node = nodeLabel(turn.node);
  return (
    <dl className="rows">
      <Row label="Last overlap" labelJa="重なり">
        <span className="metric-sm">{formatCount(turn.overlap_ms)} ms</span>
      </Row>
      <Row label="Characters" labelJa="文字数">
        <span className="metric-sm">{turn.characters}</span>
      </Row>
      <Row label="Score" labelJa="スコア">
        <span className="metric-sm">
          {formatScore(turn.score)} / {formatScore(turn.threshold)}
        </span>
      </Row>
      <Row label="Decision" labelJa="判定">
        <Pill
          tone={turn.verdict === "backchannel" ? "info" : "caution"}
          label={turn.verdict === "backchannel" ? "Backchannel" : "Interruption"}
        />
      </Row>
      <Row label="Flow step" labelJa="ステップ">
        {node.en} <code className="caption">{turn.node}</code>
      </Row>
    </dl>
  );
}

export function TurnCard({ turn }: { turn: TurnAssessed | null }) {
  if (turn === null) {
    return (
      <Card
        id="turn"
        title="Turn"
        titleJa="ターン"
        summary="Nothing yet. Talk over Kenji and this card shows how he decides."
        isEmpty
      />
    );
  }
  return (
    <Card id="turn" title="Turn" titleJa="ターン" summary={summary(turn)}>
      <BudgetBar
        value={turn.score}
        scale={1}
        marker={turn.threshold}
        markerLabel={`Interrupts at ${formatScore(turn.threshold)}`}
        fill="ink"
        label="Interruption score"
      />
      <Details turn={turn} />
    </Card>
  );
}
