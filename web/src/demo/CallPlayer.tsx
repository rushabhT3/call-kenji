import { formatClock, isoDuration } from "../format.ts";
import { Button } from "../ui/Button.tsx";
import { PlayerTrack } from "./PlayerTrack.tsx";
import type { ReplayPlayer } from "./useReplay.ts";

interface CallPlayerProps {
  player: ReplayPlayer;
}

function soundNote(player: ReplayPlayer): string | null {
  switch (player.sound) {
    case "loading":
      return "Loading both voices…";
    case "failed":
      return "The sound did not load, so the call plays without it.";
    case "off":
      return player.rate === 1
        ? "This recording has no sound."
        : `Replaying at ${String(player.rate)}× speed, without sound.`;
    case "on":
      return player.positionMs === 0 && !player.isPlaying
        ? "Press Play to hear both voices, or tap the waveform to jump to any moment."
        : null;
  }
}

function playerNote(player: ReplayPlayer): string | null {
  if (player.recording === "loading") {
    return "Loading the recorded call…";
  }
  if (player.recording === "failed") {
    return "The recorded call did not load. Reload the page to try again.";
  }
  if (player.isPlayRefused) {
    return "The browser would not start the sound. Press Play to try again.";
  }
  return soundNote(player);
}

function PlayButton({ player, canPlay }: CallPlayerProps & { canPlay: boolean }) {
  return (
    <Button
      variant="primary"
      icon={player.isPlaying ? "pause" : "play"}
      isBusy={!canPlay && player.recording !== "failed"}
      aria-disabled={!canPlay}
      onClick={canPlay ? player.togglePlay : undefined}
    >
      {player.isPlaying ? "Pause" : "Play"}
    </Button>
  );
}

function SpeakerKey() {
  return (
    <ul className="call-player__key" aria-hidden="true">
      <li className="call-player__speaker call-player__speaker--kenji">Kenji</li>
      <li className="call-player__speaker call-player__speaker--caller">Caller</li>
    </ul>
  );
}

/** Plays the recorded call with both voices, and moves the X-ray to wherever it is played. */
export function CallPlayer({ player }: CallPlayerProps) {
  const canPlay = player.recording === "ready" && player.sound !== "loading";
  return (
    <section className="call-player" aria-label="Recorded call">
      <PlayButton player={player} canPlay={canPlay} />
      <p className="metric-sm call-player__clock">
        <time dateTime={isoDuration(player.positionMs)}>{formatClock(player.positionMs)}</time>
        {" / "}
        <time dateTime={isoDuration(player.durationMs)}>{formatClock(player.durationMs)}</time>
      </p>
      <PlayerTrack player={player} canSeek={canPlay} />
      <SpeakerKey />
      <p className="call-player__note" aria-live="polite">
        {playerNote(player)}
      </p>
    </section>
  );
}
