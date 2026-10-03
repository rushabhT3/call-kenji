import { DESTINATIONS } from "./pitchContent.ts";

export function CallStop() {
  return (
    <div className="stop-body call-stop">
      <p className="stop-lead">
        No Japanese needed: pick who you play, press Say it, and watch the X-ray while Kenji
        answers.
      </p>
      <nav className="call-stop__links" aria-label="Where next">
        {DESTINATIONS.map((destination) => (
          <a
            key={destination.href}
            className={
              destination.isPrimary ? "comic-button comic-button--primary" : "comic-button"
            }
            href={destination.href}
          >
            {destination.label}
          </a>
        ))}
      </nav>
      <p className="call-stop__byline">Rushabh Trivedi · designed and built end to end</p>
    </div>
  );
}
