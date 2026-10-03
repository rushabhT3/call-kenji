import { Burst } from "../showcase/Burst.tsx";
import { STATS, type Stat } from "../showcase/content.ts";
import { EVIDENCE } from "./pitchContent.ts";

const SEED_STEP = 7;

function formatStat(stat: Stat): string {
  return `${stat.prefix ?? ""}${stat.value.toFixed(stat.decimals)}${stat.suffix ?? ""}`;
}

export function ProofStop() {
  return (
    <div className="stop-body">
      <ul className="proof-bursts">
        {STATS.map((stat, index) => (
          <li key={stat.label} className="proof-burst">
            <Burst className="proof-burst__shape" seed={index * SEED_STEP + 3}>
              <span className="proof-burst__value">{formatStat(stat)}</span>
            </Burst>
            <span className="proof-burst__label">{stat.label}</span>
          </li>
        ))}
      </ul>
      <ul className="fact-list fact-list--columns">
        {EVIDENCE.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
    </div>
  );
}
