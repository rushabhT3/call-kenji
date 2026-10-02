import { ButtonLink } from "../ui/ButtonLink.tsx";

/** The way on from a finished call: back to the start, where a new call begins. */
export function NextCall({ isDemo }: { isDemo: boolean }) {
  return (
    <div className="post-call__next">
      <ButtonLink href="/" variant="primary" size="lg" icon="phone">
        {isDemo ? "Call Kenji yourself" : "Call again"}
      </ButtonLink>
    </div>
  );
}
