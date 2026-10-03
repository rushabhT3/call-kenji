import type { MouseEvent } from "react";
import { ButtonLink } from "../ui/ButtonLink.tsx";

const CALL_PANEL_URL = "/#call";

/**
 * A finished call is shown at the landing page's own address, so a link there would only move to
 * the fragment and leave the ended call on screen. Reloading starts a fresh page at the call panel,
 * with the chosen persona remembered; the old scroll position is not restored over it.
 */
function reloadAtCallPanel(event: MouseEvent<HTMLAnchorElement>): void {
  event.preventDefault();
  window.history.scrollRestoration = "manual";
  window.history.replaceState(null, "", CALL_PANEL_URL);
  window.location.reload();
}

/** The ways on from a finished call, so nobody has to edit the address bar. */
export function NextCall({ isDemo }: { isDemo: boolean }) {
  return (
    <nav className="post-call__next" aria-label="What next">
      <ButtonLink
        href={CALL_PANEL_URL}
        variant="primary"
        size="lg"
        icon="phone"
        onClick={isDemo ? undefined : reloadAtCallPanel}
      >
        {isDemo ? "Call Kenji yourself" : "Call again"}
      </ButtonLink>
      <ButtonLink href="/?demo=1" size="lg">
        {isDemo ? "Watch again" : "Watch the demo"}
      </ButtonLink>
      <ButtonLink href="/" variant="quiet" size="lg">
        Home
      </ButtonLink>
    </nav>
  );
}
