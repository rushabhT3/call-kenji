import { CallPlayer } from "../demo/CallPlayer.tsx";
import { useReplayPlayer } from "../demo/replayContext.ts";
import { ButtonLink } from "../ui/ButtonLink.tsx";

/** Says the replay is a recording, offers the way out of it, and plays it with both voices. */
export function DemoBanner() {
  const player = useReplayPlayer();
  return (
    <>
      <aside className="demo-banner" aria-label="About this replay">
        <p className="demo-banner__text">
          A recorded call between Kenji and a synthetic caller voice. Nothing on this page is live.
        </p>
        <div className="demo-banner__actions">
          <ButtonLink href="/#call" variant="primary" size="sm" icon="phone">
            Call Kenji yourself
          </ButtonLink>
          <ButtonLink href="/" variant="quiet" size="sm">
            Home
          </ButtonLink>
        </div>
      </aside>
      {player ? <CallPlayer player={player} /> : null}
    </>
  );
}
