import { ButtonLink } from "../ui/ButtonLink.tsx";

/** The ways on from a finished call, so nobody has to edit the address bar. */
export function NextCall({ isDemo }: { isDemo: boolean }) {
  return (
    <nav className="post-call__next" aria-label="What next">
      <ButtonLink href="/#call" variant="primary" size="lg" icon="phone">
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
