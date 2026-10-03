import { TurnFlow } from "./TurnFlow.tsx";

export function TurnTaking() {
  return (
    <section className="showcase-section" aria-labelledby="turns-title">
      <div className="showcase__container showcase-split showcase-split--diagram">
        <div>
          <p className="comic-label">Turn-taking in Japanese</p>
          <h2 id="turns-title" className="showcase-heading">
            Japanese doesn't stop where you'd think
          </h2>
          <p className="showcase-lead">
            Callers say はい and ええ all the time while the other person talks, and a pause after
            「生年月日は、」 doesn't mean they've finished. Word-count rules split on spaces, and
            Japanese has none, so Kenji counts characters and knows the aizuchi.
          </p>
          <p className="showcase-lead">
            Three listeners decide when you've finished: Soniox from your words, Smart Turn from
            your voice, and a particle rule from the grammar. And if you need time to think, the
            Hold button beats all three.
          </p>
        </div>
        <div className="showcase-diagram">
          <TurnFlow />
        </div>
      </div>
    </section>
  );
}
