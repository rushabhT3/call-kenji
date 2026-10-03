import { Burst } from "./Burst.tsx";
import { Doodles } from "./Doodles.tsx";

const AUDIENCES = [
  { who: "Founder or CEO?", what: "What it proves", href: "#proves" },
  { who: "Engineer?", what: "How it's fast", href: "#fast" },
  { who: "Hiring?", what: "What I did", href: "#built" },
] as const;

function AudienceLinks() {
  return (
    <nav className="showcase-hero__audiences" aria-label="Jump to">
      {AUDIENCES.map((audience) => (
        <a key={audience.href} className="audience-chip" href={audience.href}>
          <span>{audience.who}</span> {audience.what} →
        </a>
      ))}
    </nav>
  );
}

export function ShowcaseHero() {
  return (
    <section className="showcase-hero" aria-labelledby="showcase-title">
      <Doodles />
      <div className="showcase__container showcase-hero__inner">
        <Burst className="showcase-hero__burst" seed={11}>
          <p className="burst__word">Call Kenji!</p>
          <p className="burst__ja comic-ja" lang="ja">
            ケンジに電話
          </p>
        </Burst>
        <h1 id="showcase-title" className="showcase-hero__title">
          A Japanese voice agent that starts answering in about 0.7 seconds, on a model that needs 2
          to 6.
        </h1>
        <p className="showcase-hero__lead">
          I built Kenji, a debt-collection agent for a fictional Tokyo servicer. He speaks Japanese,
          follows Japan's lending law, and puts every decision he makes on screen while you talk to
          him. This page is how it works, and the tricks that make a heavy reasoning model feel
          instant.
        </p>
        <p className="showcase-hero__byline">Rushabh Trivedi · designed and built end to end</p>
        <div className="showcase-hero__actions">
          <a className="comic-button comic-button--primary" href="/#call">
            Call Kenji
          </a>
          <a className="comic-button" href="/?demo=1">
            Watch a real call
          </a>
        </div>
        <AudienceLinks />
      </div>
    </section>
  );
}
