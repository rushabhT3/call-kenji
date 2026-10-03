import type { CSSProperties, KeyboardEvent, PointerEvent } from "react";
import { formatClock } from "../format.ts";
import { keyedPosition, positionAtPointer } from "./playhead.ts";
import type { SpeakerRegion } from "./speakerRegions.ts";
import type { ReplayPlayer } from "./useReplay.ts";

const MILLISECONDS_PER_SECOND = 1000;
const PERCENT = 100;

interface PlayerTrackProps {
  player: ReplayPlayer;
  canSeek: boolean;
}

function share(partMs: number, wholeMs: number): string {
  return wholeMs > 0 ? `${String((partMs / wholeMs) * PERCENT)}%` : "0%";
}

function SpeakerBands({
  regions,
  durationMs,
}: {
  regions: readonly SpeakerRegion[];
  durationMs: number;
}) {
  return (
    <div className="speaker-bands" aria-hidden="true">
      {regions.map((region) => (
        <span
          key={region.lineId}
          className={`speaker-bands__band speaker-bands__band--${region.speaker}`}
          style={
            {
              "--start": share(region.startMs, durationMs),
              "--length": share(region.endMs - region.startMs, durationMs),
            } as CSSProperties
          }
        />
      ))}
    </div>
  );
}

/** Where the recording's waveform is drawn, once it has sound to draw. */
function Waveform({ onElement }: { onElement: (element: HTMLElement | null) => void }) {
  return <div ref={onElement} className="call-player__waveform" />;
}

/** Click, drag or use the arrow keys to move through the call. */
function seekingHandlers({ player, canSeek }: PlayerTrackProps) {
  const seekToPointer = (event: PointerEvent<HTMLDivElement>) => {
    const track = event.currentTarget.getBoundingClientRect();
    player.seek(positionAtPointer(event.clientX, track, player.durationMs));
  };
  return {
    onPointerDown: (event: PointerEvent<HTMLDivElement>) => {
      if (canSeek) {
        event.currentTarget.setPointerCapture(event.pointerId);
        seekToPointer(event);
      }
    },
    onPointerMove: (event: PointerEvent<HTMLDivElement>) => {
      if (canSeek && event.currentTarget.hasPointerCapture(event.pointerId)) {
        seekToPointer(event);
      }
    },
    onKeyDown: (event: KeyboardEvent<HTMLDivElement>) => {
      const target = keyedPosition(event.key, player.positionMs, player.durationMs);
      if (canSeek && target !== null) {
        event.preventDefault();
        player.seek(target);
      }
    },
  };
}

/**
 * The whole call on one line: who speaks when, the waveform when there is sound, and how far
 * the replay has got. It is the slider that moves the replay.
 */
export function PlayerTrack({ player, canSeek }: PlayerTrackProps) {
  const { positionMs, durationMs } = player;
  const hasWaveform = player.sound === "loading" || player.sound === "on";
  const handlers = seekingHandlers({ player, canSeek });
  return (
    <div
      className="call-player__track"
      role="slider"
      tabIndex={0}
      aria-label="Position in the call"
      aria-disabled={!canSeek}
      aria-valuemin={0}
      aria-valuemax={Math.round(durationMs / MILLISECONDS_PER_SECOND)}
      aria-valuenow={Math.floor(positionMs / MILLISECONDS_PER_SECOND)}
      aria-valuetext={`${formatClock(positionMs)} of ${formatClock(durationMs)}`}
      style={{ "--played": share(positionMs, durationMs) } as CSSProperties}
      {...handlers}
    >
      <SpeakerBands regions={player.regions} durationMs={durationMs} />
      {hasWaveform ? (
        <Waveform onElement={player.attachWaveform} />
      ) : (
        <div className="call-player__played" aria-hidden="true" />
      )}
    </div>
  );
}
