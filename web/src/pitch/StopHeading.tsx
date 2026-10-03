import { Burst } from "../showcase/Burst.tsx";
import type { StopData } from "./stops.ts";

interface StopHeadingProps {
  stop: StopData;
  number: number;
}

/** A numbered starburst, the stop's Japanese name and its title, the same on every stop. */
export function StopHeading({ stop, number }: StopHeadingProps) {
  return (
    <header className="stop-heading">
      <Burst className="stop-heading__badge" seed={number * 5 + 1}>
        <span className="stop-heading__number" aria-hidden="true">
          {number}
        </span>
      </Burst>
      <div className="stop-heading__text">
        <p className="comic-label">
          Stop {number} · <span lang="ja">{stop.ja}</span>
        </p>
        <h2 id={`stop-${stop.id}-title`} className="stop-heading__title">
          {stop.title}
        </h2>
      </div>
    </header>
  );
}
