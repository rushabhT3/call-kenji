import type { TranscriptEntry } from "../call/callView.ts";
import { formatClock, isoDuration } from "../format.ts";

interface TranscriptLineProps {
  line: TranscriptEntry;
  offsetMs: number;
  subtitle: string | undefined;
  isCurrent: boolean;
}

const SPEAKERS = {
  kenji: { en: "Kenji", ja: "ケンジ" },
  caller: { en: "You", ja: "あなた" },
} as const;

export function TranscriptLine({ line, offsetMs, subtitle, isCurrent }: TranscriptLineProps) {
  const speaker = SPEAKERS[line.speaker];
  const classes = [
    "line",
    `line--${line.speaker}`,
    isCurrent ? "line--current" : "",
    line.isBackchannel ? "line--backchannel" : "",
  ];
  return (
    <li className={classes.join(" ").trim()}>
      <p className="caption line__meta">
        <span className="line__speaker">
          {speaker.en} <span lang="ja">{speaker.ja}</span>
        </span>
        <time dateTime={isoDuration(offsetMs)}>{formatClock(offsetMs)}</time>
      </p>
      <div className="line__text">
        <p className="line__ja" lang="ja">
          {line.ja}
        </p>
        <p className="line__en" lang="en">
          {line.isBackchannel
            ? "Aizuchi while Kenji spoke. He kept going."
            : (subtitle ?? "Translating…")}
        </p>
      </div>
    </li>
  );
}
