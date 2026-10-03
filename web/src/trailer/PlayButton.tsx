interface PlayButtonProps {
  onPlay: () => void;
}

/** The big comic play button laid over the poster until the trailer first plays. */
export function PlayButton({ onPlay }: PlayButtonProps) {
  return (
    <button type="button" className="trailer-play" onClick={onPlay}>
      <span className="trailer-play__disc" aria-hidden="true">
        <svg className="trailer-play__icon" viewBox="0 0 24 24" focusable="false">
          <path d="M8 5.5v13l10.5-6.5z" />
        </svg>
      </span>
      <span className="trailer-play__label">Play the trailer</span>
    </button>
  );
}
