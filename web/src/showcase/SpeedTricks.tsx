import { SPEED_TRICKS } from "./content.ts";
import { LatencyChart } from "./LatencyChart.tsx";

export function SpeedTricks() {
  return (
    <section id="fast" className="showcase-section" aria-labelledby="fast-title">
      <div className="showcase__container">
        <p className="comic-label">For engineers</p>
        <h2 id="fast-title" className="showcase-heading">
          How I made a slow model feel fast
        </h2>
        <p className="showcase-lead">
          Kenji's brain is Meta's Muse Spark, a reasoning model whose thinking can't be switched
          off: it takes 2 to 6 seconds to say anything. That is a long silence on a phone call. So I
          stopped making callers wait for it.
        </p>
      </div>
      <div className="showcase__container speed">
        <ol className="speed__tricks">
          {SPEED_TRICKS.map((trick, index) => (
            <li key={trick.title} className="trick comic-panel comic-reveal">
              <span className="trick__number" aria-hidden="true">
                {index + 1}
              </span>
              <h3 className="trick__title">{trick.title}</h3>
              <p>{trick.text}</p>
            </li>
          ))}
        </ol>
        <div className="speed__chart">
          <LatencyChart />
        </div>
      </div>
    </section>
  );
}
