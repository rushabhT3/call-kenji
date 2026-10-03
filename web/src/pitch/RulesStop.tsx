import { REFUSAL, SAFEGUARDS, type Exchange } from "./pitchContent.ts";

function Bubble({ line, speaker }: { line: Exchange; speaker: "caller" | "kenji" }) {
  return (
    <blockquote className={`speech__bubble speech__bubble--${speaker}`}>
      <p className="comic-ja" lang="ja">
        {line.ja}
      </p>
      <p className="speech__en">{line.en}</p>
    </blockquote>
  );
}

export function RulesStop() {
  return (
    <div className="stop-body stop-body--split">
      <div>
        <p className="stop-lead">
          The model can only act through tools that check the terms, so it cannot agree to ¥3,000 a
          month however hard you push.
        </p>
        <ul className="stamp-list" aria-label="Safeguards checked on every call">
          {SAFEGUARDS.map((safeguard) => (
            <li key={safeguard.name} className="stamp">
              <span className="stamp__mark" aria-hidden="true">
                ✓ Pass
              </span>
              {safeguard.name} · <span lang="ja">{safeguard.ja}</span>
            </li>
          ))}
        </ul>
      </div>
      <figure className="speech">
        <figcaption className="comic-label">From the recorded demo call</figcaption>
        <Bubble line={REFUSAL.caller} speaker="caller" />
        <Bubble line={REFUSAL.kenji} speaker="kenji" />
      </figure>
    </div>
  );
}
