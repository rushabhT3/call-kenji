import { ButtonLink } from "../ui/ButtonLink.tsx";

/** Says the replay is a recording and offers the way out of it, for the whole replay. */
export function DemoBanner() {
  return (
    <aside className="demo-banner" aria-label="About this replay">
      <p className="demo-banner__text">A recorded call, replayed. Nothing on this page is live.</p>
      <div className="demo-banner__actions">
        <ButtonLink href="/#call" variant="primary" size="sm" icon="phone">
          Call Kenji yourself
        </ButtonLink>
        <ButtonLink href="/" variant="quiet" size="sm">
          Home
        </ButtonLink>
      </div>
    </aside>
  );
}
