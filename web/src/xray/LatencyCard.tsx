import type { LatencyMeasured } from "../contract/events.ts";
import { formatCount } from "../format.ts";
import { BudgetBar } from "../ui/BudgetBar.tsx";
import { Card } from "../ui/Card.tsx";
import { Pill } from "../ui/Pill.tsx";
import { LatencyHistory } from "./LatencyHistory.tsx";

const SCALE_MS = 2000;

function Stages({ latest, scale }: { latest: LatencyMeasured; scale: number }) {
  const stages = [
    { label: "End of turn", ja: "発話終了の判定", value: latest.end_of_turn_ms },
    { label: "LLM first token", ja: "LLM最初のトークン", value: latest.llm_first_token_ms },
    { label: "TTS first audio", ja: "音声の開始", value: latest.tts_first_audio_ms },
  ];
  return (
    <ul className="stages">
      {stages.map((stage) => (
        <li key={stage.label} className="stage">
          <span className="caption">
            {stage.label} · <span lang="ja">{stage.ja}</span>
          </span>
          <span className="stage__row">
            <BudgetBar
              value={stage.value}
              scale={scale}
              marker={latest.budget_ms}
              markerLabel=""
              fill="ink"
              label={stage.label}
            />
            <span className="metric-sm stage__value">{formatCount(stage.value)} ms</span>
          </span>
        </li>
      ))}
    </ul>
  );
}

function Headline({ latest }: { latest: LatencyMeasured }) {
  const isWithin = latest.total_ms <= latest.budget_ms;
  const over = Math.round(latest.total_ms - latest.budget_ms);
  return (
    <>
      <p className="metric">
        <span className="metric__value numeric">{formatCount(latest.total_ms)}</span>
        <span className="caption">ms</span>
      </p>
      <BudgetBar
        value={latest.total_ms}
        scale={Math.max(SCALE_MS, latest.total_ms)}
        marker={latest.budget_ms}
        markerLabel={`${formatCount(latest.budget_ms)} ms budget`}
        fill={isWithin ? "success" : "danger"}
        label="Last reply"
      />
      <Pill
        tone={isWithin ? "pass" : "blocked"}
        label={isWithin ? "Within budget" : `Over budget by ${formatCount(over)} ms`}
      />
    </>
  );
}

function summary(latest: LatencyMeasured): string {
  const verdict = latest.total_ms <= latest.budget_ms ? "within" : "over";
  return `Last reply in ${formatCount(latest.total_ms)} ms, ${verdict} the ${formatCount(latest.budget_ms)} ms budget.`;
}

export function LatencyCard({ turns }: { turns: readonly LatencyMeasured[] }) {
  const latest = turns.at(-1);
  if (latest === undefined) {
    return (
      <Card
        id="latency"
        title="Latency"
        titleJa="応答時間"
        summary="Waiting for the first reply."
        isEmpty
      />
    );
  }
  return (
    <Card id="latency" title="Latency" titleJa="応答時間" summary={summary(latest)}>
      <Headline latest={latest} />
      <Stages latest={latest} scale={Math.max(SCALE_MS, latest.total_ms)} />
      <p className="metric-sm latency__percentiles">
        P50 {formatCount(latest.p50_ms)} ms · P95 {formatCount(latest.p95_ms)} ms · {latest.turn}{" "}
        turns
      </p>
      <LatencyHistory turns={turns} />
    </Card>
  );
}
