import { STACK } from "../showcase/stack.ts";

export function StackStop() {
  return (
    <div className="stop-body">
      <p className="stop-lead">
        Standing on great open source and a few sharp services. The glue, the rules, the turn
        handling, the speed tricks and the X-ray are mine.
      </p>
      <ul className="stack-wall">
        {STACK.map((item) => (
          <li
            key={item.name}
            className={`stack-tile stack-tile--${item.kind === "service" ? "service" : "open"}`}
          >
            <span className="stack-tile__name">{item.name}</span>
            <span className="stack-tile__role">{item.role}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
