import { useState } from "react";
import {
  currentKenjiLineId,
  elapsedMs,
  type CallView,
  type TranscriptEntry,
} from "../call/callView.ts";
import { transcriptSummary } from "../call/copy.ts";
import { useLinePlayer } from "../demo/replayContext.ts";
import { Button } from "../ui/Button.tsx";
import { Card } from "../ui/Card.tsx";
import { TranscriptLine } from "./TranscriptLine.tsx";

/**
 * During a call the card keeps to the latest lines, as captions do, so it never needs a scroll
 * box of its own inside the scrolling page; the earlier lines are one press away.
 */
export const LIVE_LINES = 3;

function ListeningRow({ text }: { text: string | null }) {
  return (
    <p className="listening" aria-hidden="true">
      <span className="caption">Listening</span>
      <span className="listening__text" lang="ja">
        {text}
        <span className="cursor" />
      </span>
    </p>
  );
}

function linesToShow(view: CallView, isShowingAll: boolean): TranscriptEntry[] {
  const finished = view.lines;
  if (view.status !== "live" || isShowingAll) {
    return finished;
  }
  return finished.slice(Math.max(0, finished.length - LIVE_LINES));
}

function speakingEntry(view: CallView): TranscriptEntry | null {
  const speaking = view.speaking;
  return speaking
    ? {
        lineId: speaking.lineId,
        speaker: "kenji",
        ja: speaking.ja,
        isBackchannel: false,
        at: speaking.at,
      }
    : null;
}

interface EarlierLinesToggleProps {
  hiddenCount: number;
  isShowingAll: boolean;
  onToggle: () => void;
}

function EarlierLinesToggle({ hiddenCount, isShowingAll, onToggle }: EarlierLinesToggleProps) {
  const label = isShowingAll
    ? "Show the latest lines only"
    : `Show ${String(hiddenCount)} earlier ${hiddenCount === 1 ? "line" : "lines"}`;
  return (
    <Button variant="quiet" size="sm" aria-expanded={isShowingAll} onClick={onToggle}>
      {label}
    </Button>
  );
}

interface TranscriptLogProps {
  view: CallView;
  lines: TranscriptEntry[];
}

function TranscriptLog({ view, lines }: TranscriptLogProps) {
  const speaking = speakingEntry(view);
  const currentId = currentKenjiLineId(view);
  const startedAt = view.startedAt;
  const offset = (line: TranscriptEntry) => (startedAt ? elapsedMs(startedAt, line.at) : 0);
  const playLine = useLinePlayer();
  return (
    <div role="log" aria-live="polite" aria-relevant="additions" aria-label="Call transcript">
      <ol className="transcript__log">
        {lines.map((line) => (
          <TranscriptLine
            key={line.lineId}
            line={line}
            offsetMs={offset(line)}
            subtitle={view.subtitles[line.lineId]}
            isCurrent={line.lineId === currentId}
            tone={view.tones[line.lineId]}
            onPlay={playLine}
          />
        ))}
        {speaking ? (
          <TranscriptLine
            key={speaking.lineId}
            line={speaking}
            offsetMs={offset(speaking)}
            subtitle={view.subtitles[speaking.lineId]}
            isCurrent
            isSpeaking
            onPlay={playLine}
          />
        ) : null}
      </ol>
    </div>
  );
}

export function Transcript({ view }: { view: CallView }) {
  const [isShowingAll, setIsShowingAll] = useState(false);
  const isLive = view.status === "live";
  const shown = linesToShow(view, isShowingAll);
  const hiddenCount = view.lines.length - shown.length;
  return (
    <Card
      id="transcript"
      title="Transcript"
      titleJa="通話記録"
      summary={transcriptSummary(view.status, view.lines.length)}
      isEmpty={view.status === "waiting"}
      className="transcript"
    >
      {isLive && (hiddenCount > 0 || isShowingAll) ? (
        <EarlierLinesToggle
          hiddenCount={hiddenCount}
          isShowingAll={isShowingAll}
          onToggle={() => {
            setIsShowingAll(!isShowingAll);
          }}
        />
      ) : null}
      <TranscriptLog view={view} lines={shown} />
      {isLive ? <ListeningRow text={view.partial?.ja ?? null} /> : null}
    </Card>
  );
}
