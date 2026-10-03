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

export function TranscriptLine({
  line,
  offsetMs,
  subtitle,
  isCurrent,
  isSpeaking = false,
  tone,
}: TranscriptLineProps) {
  const speaker = SPEAKERS[line.speaker];
  const badge = tone ? toneBadge(tone) : null;
  const classes = [
    "line",
    `line--${line.speaker}`,
    isCurrent ? "line--current" : "",
    line.isBackchannel ? "line--backchannel" : "",
    isSpeaking ? "line--speaking" : "",
  ];
  return (
    <li className={classes.join(" ").trim()}>
      <p className="caption line__meta">
        <span className="line__speaker">
          {speaker.en} <span lang="ja">{speaker.ja}</span>
        </span>
        <time dateTime={isoDuration(offsetMs)}>{formatClock(offsetMs)}</time>
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
