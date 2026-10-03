import { Burst } from "./Burst.tsx";

export function FinalCall() {
  return (
    <section className="final-call" aria-labelledby="final-call-title">
      <div className="showcase__container final-call__inner">
        <Burst className="final-call__burst" seed={29}>
          <h2 id="final-call-title" className="burst__word">
            Your turn!
          </h2>
        </Burst>
        <p className="showcase-lead">
          No Japanese needed: pick who you play, press Say it, and watch the X-ray while Kenji
          answers.
        </p>
        <div className="showcase-hero__actions">
          <a className="comic-button comic-button--primary" href="/#call">
            Call Kenji
          </a>
          <a className="comic-button" href="/?demo=1">
            Watch the demo
          </a>
        </div>
      </div>
    </section>
  );
}
