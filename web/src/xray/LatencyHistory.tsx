import type { CSSProperties } from "react";
import type { LatencyMeasured } from "../contract/events.ts";
import { formatCount } from "../format.ts";

const HISTORY_TURNS = 12;
const SCALE_MS = 2000;

const percent = (value: number) => `${String(Math.min(100, (value / SCALE_MS) * 100))}%`;

export function LatencyHistory({ turns }: { turns: readonly LatencyMeasured[] }) {
  const recent = turns.slice(-HISTORY_TURNS);
  const budget = recent.at(-1)?.budget_ms ?? 0;
  return (
    <>
      <div
        className="history"
        aria-hidden="true"
        style={{ "--budget": percent(budget) } as CSSProperties}
      >
        {recent.map((turn) => (
          <span
            key={turn.turn}
            className={
              turn.total_ms > turn.budget_ms ? "history__bar history__bar--over" : "history__bar"
            }
            style={{ "--value": percent(turn.total_ms) } as CSSProperties}
          />
        ))}
      </div>
      <table className="visually-hidden">
        <caption>Reply time per turn</caption>
        <tbody>
          {recent.map((turn) => (
            <tr key={turn.turn}>
              <th scope="row">Turn {turn.turn}</th>
              <td>{formatCount(turn.total_ms)} ms</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
