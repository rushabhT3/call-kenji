import { SPEED_TRICKS } from "../showcase/content.ts";
import { LatencyChart } from "../showcase/LatencyChart.tsx";

export function SpeedStop() {
  return (
    <div className="stop-body stop-body--split">
      <div>
        <p className="stop-lead">
          Kenji's brain is Meta's Muse Spark, a reasoning model whose thinking can't be switched
          off: it takes 2 to 6 seconds to say anything. So callers never wait for it.
        </p>
        <ol className="trick-list">
          {SPEED_TRICKS.map((trick) => (
            <li key={trick.title}>
              <h3 className="trick-list__title">{trick.title}</h3>
              <p>{trick.text}</p>
            </li>
          ))}
        </ol>
      </div>
      <div className="stop-diagram">
        <LatencyChart />
      </div>
    </div>
  );
}
