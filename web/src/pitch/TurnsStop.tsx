import { TurnFlow } from "../showcase/TurnFlow.tsx";

export function TurnsStop() {
  return (
    <div className="stop-body stop-body--split">
      <div>
        <p className="stop-lead">
          Word-count rules split on spaces, and Japanese has none. Kenji counts characters, knows
          the aizuchi, and holds a turn open when it stops on a particle.
        </p>
        <p className="stop-text">
          Three listeners decide when you have finished: Soniox from your words, Smart Turn v3 from
          your voice, and a particle rule from the grammar. If you need time to think, the Hold
          button beats all three.
        </p>
      </div>
      <div className="stop-diagram stop-diagram--tall">
        <TurnFlow />
      </div>
    </div>
  );
}
