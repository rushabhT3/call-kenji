import { Burst } from "./Burst.tsx";
import { STATS, type Stat } from "./content.ts";

function formatStat(stat: Stat): string {
  return `${stat.prefix ?? ""}${stat.value.toFixed(stat.decimals)}${stat.suffix ?? ""}`;
}

export function StatStrip() {
  return (
    <section className="stat-strip" aria-label="In numbers">
      <ul className="showcase__container stat-strip__list">
        {STATS.map((stat, index) => (
          <li key={stat.label} className="stat">
            <Burst className="stat__burst" seed={index * 7 + 2}>
              <span
                className="stat__value"
                aria-hidden="true"
                data-value={stat.value}
                data-decimals={stat.decimals}
                data-prefix={stat.prefix ?? ""}
                data-suffix={stat.suffix ?? ""}
              >
                {formatStat(stat)}
              </span>
              <span className="visually-hidden">{formatStat(stat)}</span>
            </Burst>
            <p className="stat__label">{stat.label}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
