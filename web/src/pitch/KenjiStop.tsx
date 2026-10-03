import { GREETING, KENJI_FACTS } from "./pitchContent.ts";

export function KenjiStop() {
  return (
    <div className="stop-body stop-body--split">
      <div>
        <p className="stop-lead">
          An AI agent for a fictional Japanese debt servicer, <span lang="ja">みなと債権回収</span>.
          You play the customer in your browser and watch him decide.
        </p>
        <ul className="fact-list">
          {KENJI_FACTS.map((fact) => (
            <li key={fact}>{fact}</li>
          ))}
        </ul>
      </div>
      <figure className="speech">
        <figcaption className="comic-label">His first words, from a recorded call</figcaption>
        <blockquote className="speech__bubble">
          <p className="comic-ja" lang="ja">
            {GREETING.ja}
          </p>
          <p className="speech__en">{GREETING.en}</p>
        </blockquote>
      </figure>
    </div>
  );
}
