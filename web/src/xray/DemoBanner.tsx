import type { DemoSound } from "../call/useDemoSound.ts";
import { Button } from "../ui/Button.tsx";
import { ButtonLink } from "../ui/ButtonLink.tsx";

/** Says the replay is a recording, plays its sound on request, and offers the way out of it. */
export function DemoBanner({ sound }: { sound: DemoSound | null }) {
  return (
    <aside className="demo-banner" aria-label="About this replay">
      <p className="demo-banner__text">
        A recorded call between Kenji and a synthetic caller voice. Nothing on this page is live.
      </p>
      <div className="demo-banner__actions">
        {sound ? (
          <Button size="sm" icon="sound" aria-pressed={sound.isOn} onClick={sound.toggle}>
            {sound.isOn ? "Sound off" : "Sound on"}
          </Button>
        ) : null}
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
