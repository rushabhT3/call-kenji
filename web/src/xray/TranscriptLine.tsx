import type { TranscriptEntry } from "../call/callView.ts";
import { toneBadge } from "../call/copy.ts";
import type { CallerToneHeard } from "../contract/events.ts";
import { formatClock, isoDuration } from "../format.ts";
import { Pill } from "../ui/Pill.tsx";

interface TranscriptLineProps {
  line: TranscriptEntry;
  offsetMs: number;
  /** English for the line; null when its translation failed for good. */
  subtitle: string | null | undefined;
  isCurrent: boolean;
  /** Kenji is still saying this line: its English may follow when he finishes. */
  isSpeaking?: boolean;
  /** How the caller sounded on this line, once it has been heard. */
  tone?: CallerToneHeard | undefined;
  /** Plays a recorded call from a line; null or absent when the call is live. */
  onPlay?: ((lineId: string) => void) | null;
}

const SPEAKERS = {
  kenji: { en: "Kenji", ja: "ケンジ" },
  caller: { en: "You", ja: "あなた" },
} as const;

function englishFor(
  line: TranscriptEntry,
  subtitle: string | null | undefined,
  isSpeaking: boolean,
) {
  if (line.isBackchannel) {
    return "Aizuchi while Kenji spoke. He kept going.";
  }
  if (subtitle === null) {
    return "No English for this line: the translation did not come back.";
  }
  return subtitle ?? (isSpeaking ? "" : "Translating…");
}

interface LineTimeProps {
  line: TranscriptEntry;
  offsetMs: number;
  onPlay: ((lineId: string) => void) | null;
}

/** When the line was said; on a recording, also the way to play the call from it. */
function LineTime({ line, offsetMs, onPlay }: LineTimeProps) {
  const time = <time dateTime={isoDuration(offsetMs)}>{formatClock(offsetMs)}</time>;
  if (onPlay === null) {
    return time;
  }
  return (
    <button
      type="button"
      className="line__play"
      onClick={() => {
        onPlay(line.lineId);
      }}
    >
      <span className="visually-hidden">Play from this line, </span>
      {time}
    </button>
  );
}

export function TranscriptLine({
  line,
  offsetMs,
  subtitle,
  isCurrent,
  isSpeaking = false,
  tone,
  onPlay = null,
}: TranscriptLineProps) {
  const speaker = SPEAKERS[line.speaker];
  const badge = tone ? toneBadge(tone) : null;
  const classes = [
    "line",
    `line--${line.speaker}`,
    isCurrent ? "line--current" : "",
    line.isBackchannel ? "line--backchannel" : "",
    isSpeaking ? "line--speaking" : "",
    onPlay ? "line--playable" : "",
  ];
  return (
    <li className={classes.join(" ").trim()}>
      <p className="caption line__meta">
        <span className="line__speaker">
          {speaker.en} <span lang="ja">{speaker.ja}</span>
        </span>
        <LineTime line={line} offsetMs={offsetMs} onPlay={onPlay} />
        {badge ? <Pill tone="info" label={badge} context="Tone" /> : null}
      </p>
      <div className="line__text">
        <p className="line__ja" lang="ja">
          {line.ja}
          {isSpeaking ? <span className="cursor" aria-hidden="true" /> : null}
        </p>
        <p className="line__en" lang="en">
          {englishFor(line, subtitle, isSpeaking)}
        </p>
      </div>
    </li>
  );
}
