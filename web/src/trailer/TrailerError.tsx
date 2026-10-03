import { PITCH_PATH } from "../pages.ts";
import { DEMO_LINK } from "./content.ts";

interface TrailerErrorProps {
  onRetry: () => void;
}

/** Shown instead of a broken player when the video file cannot be loaded. */
export function TrailerError({ onRetry }: TrailerErrorProps) {
  return (
    <section
      className="trailer-error comic-panel comic-panel--red"
      aria-labelledby="trailer-error-title"
    >
      <p className="comic-label">Projector jammed</p>
      <h2 id="trailer-error-title" className="trailer-error__title">
        The trailer is still rolling in
      </h2>
      <p className="trailer-error__text">
        The video didn't load. Try again in a minute, or meet Kenji another way while it arrives.
      </p>
      <div className="trailer-error__actions">
        <button type="button" className="comic-button comic-button--primary" onClick={onRetry}>
          Try again
        </button>
        <a className="comic-button" href={DEMO_LINK.href}>
          {DEMO_LINK.label}
        </a>
        <a className="comic-button" href={PITCH_PATH}>
          Explore Kenji's Universe
        </a>
      </div>
    </section>
  );
}
