import { PROBLEMS } from "./pitchContent.ts";

export function ProblemStop() {
  return (
    <div className="stop-body">
      <p className="stop-lead">
        Voice agents win or lose on three things a demo usually hides. Kenji puts all three on
        screen while you talk to him.
      </p>
      <ul className="problem-cards">
        {PROBLEMS.map((problem, index) => (
          <li key={problem.title} className={`problem-card problem-card--${String(index + 1)}`}>
            <h3 className="problem-card__title">{problem.title}</h3>
            <p>{problem.text}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
