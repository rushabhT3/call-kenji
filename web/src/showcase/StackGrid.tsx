import { STACK, type StackItem } from "./stack.ts";

function StackCard({ item }: { item: StackItem }) {
  return (
    <li className="stack-card comic-panel">
      <p className="stack-card__kind">{item.kind}</p>
      <h3 className="stack-card__name">
        <a href={item.href} target="_blank" rel="noreferrer">
          {item.name}
          <span className="visually-hidden"> (opens in a new tab)</span>
        </a>
      </h3>
      <p className="stack-card__role">{item.role}</p>
      <p className="stack-card__text">{item.text}</p>
    </li>
  );
}

export function StackGrid() {
  return (
    <section className="showcase-section" aria-labelledby="stack-title">
      <div className="showcase__container">
        <p className="comic-label">The stack</p>
        <h2 id="stack-title" className="showcase-heading">
          Standing on great open source
        </h2>
        <p className="showcase-lead">
          What each library and service does in a call. The glue, the rules, the turn handling, the
          speed tricks and the X-ray are mine.
        </p>
        <ul className="stack-grid">
          {STACK.map((item) => (
            <StackCard key={item.name} item={item} />
          ))}
        </ul>
      </div>
    </section>
  );
}
