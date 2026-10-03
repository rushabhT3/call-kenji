import type { PitchMoves } from "./usePitchKeys.ts";
import { isAtEnd, type Position } from "./position.ts";
import { LAST_STEP, OVERVIEW_STEP, stepLabel } from "./stops.ts";

interface PitchControlsProps {
  position: Position;
  pageCounts: readonly number[];
  isPlaying: boolean;
  moves: PitchMoves;
  onTogglePlay: () => void;
}

function Progress({ position, pages }: { position: Position; pages: number }) {
  const { step, page } = position;
  return (
    <p className="pitch-bar__progress">
      <span className="pitch-bar__count">{`${String(step)} / ${String(LAST_STEP)}`}</span>
      <span className="pitch-bar__label">
        {stepLabel(step)}
        {pages > 1 ? (
          <span className="pitch-bar__page">{` · ${String(page + 1)}/${String(pages)}`}</span>
        ) : null}
      </span>
    </p>
  );
}

function StepButtons({
  position,
  pageCounts,
  moves,
}: Omit<PitchControlsProps, "isPlaying" | "onTogglePlay">) {
  const isOverview = position.step === OVERVIEW_STEP;
  return (
    <div className="pitch-bar__steps">
      <button
        type="button"
        className="comic-button pitch-bar__button"
        aria-label="Back"
        disabled={isOverview && position.page === 0}
        onClick={moves.previous}
      >
        ◀
      </button>
      <Progress position={position} pages={pageCounts[position.step] ?? 1} />
      <button
        type="button"
        className="comic-button comic-button--primary pitch-bar__button"
        aria-label={isOverview ? "Start the pitch" : "Next"}
        disabled={isAtEnd(position, pageCounts)}
        onClick={moves.next}
      >
        {isOverview ? <span className="pitch-bar__start">Start </span> : null}▶
      </button>
    </div>
  );
}

/** The comic control strip under the universe: home, back, where you are, next, map and play. */
export function PitchControls({
  position,
  pageCounts,
  isPlaying,
  moves,
  onTogglePlay,
}: PitchControlsProps) {
  return (
    <nav className="pitch-bar" aria-label="Pitch controls">
      <a className="pitch-bar__home" href="/">
        <span aria-hidden="true">←</span> <span className="pitch-bar__home-text">Call Kenji</span>
      </a>
      <StepButtons position={position} pageCounts={pageCounts} moves={moves} />
      <div className="pitch-bar__extras">
        <button
          type="button"
          className="comic-button pitch-bar__button"
          aria-pressed={position.step === OVERVIEW_STEP}
          onClick={() => {
            moves.jump(OVERVIEW_STEP);
          }}
        >
          Map
        </button>
        <button
          type="button"
          className="comic-button pitch-bar__button"
          aria-pressed={isPlaying}
          onClick={onTogglePlay}
        >
          {isPlaying ? "Pause" : "Play"}
        </button>
      </div>
    </nav>
  );
}
