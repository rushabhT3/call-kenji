const EVIDENCE = [
  "600+ Python tests, with the rules at 100% line and branch coverage",
  "120+ web unit tests, and 80+ browser tests on desktop and phone with WCAG AA scans",
  "24 of 24 real-model conversations, rerun after every change to how Kenji behaves",
  "Strict mypy, Ruff and ESLint, and CI on every push to main and every pull request",
  "Five fictional callers to play, with lines you can have said for you",
] as const;

export function WhatIDid() {
  return (
    <section id="built" className="showcase-section" aria-labelledby="built-title">
      <div className="showcase__container showcase-split">
        <div>
          <p className="comic-label">For hiring managers</p>
          <h2 id="built-title" className="showcase-heading">
            What I did
          </h2>
          <p className="showcase-lead">
            I designed and built all of it: the Python voice server, the pure domain rules, the turn
            handling, the speed tricks, the X-ray, the evals and the CI. Every trade-off is written
            down, 52 decisions in all, each saying where it lives in the repo.
          </p>
          <p className="showcase-signature">Rushabh</p>
        </div>
        <ul className="evidence comic-panel comic-panel--red">
          {EVIDENCE.map((line) => (
            <li key={line} className="evidence__item comic-reveal">
              {line}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
