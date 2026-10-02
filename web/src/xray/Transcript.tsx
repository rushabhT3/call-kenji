import { useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { elapsedMs, latestKenjiLineId, type CallView } from "../call/callView.ts";
import { Button } from "../ui/Button.tsx";
import { TranscriptLine } from "./TranscriptLine.tsx";

const NEAR_BOTTOM_PX = 48;

function JumpToLatest({ onJump }: { onJump: () => void }) {
  return (
    <span className="transcript__jump">
      <Button size="sm" icon="arrowDown" onClick={onJump}>
        Jump to latest
      </Button>
    </span>
  );
}

interface ScrollRegionProps {
  contentKey: number;
  children: ReactNode;
}

function ScrollRegion({ contentKey, children }: ScrollRegionProps) {
  const regionRef = useRef<HTMLDivElement>(null);
  const [isAwayFromBottom, setIsAwayFromBottom] = useState(false);

  useLayoutEffect(() => {
    const region = regionRef.current;
    if (region && !isAwayFromBottom) {
      region.scrollTop = region.scrollHeight;
    }
  }, [contentKey, isAwayFromBottom]);

  const handleScroll = () => {
    const region = regionRef.current;
    if (region) {
      const distance = region.scrollHeight - region.scrollTop - region.clientHeight;
      setIsAwayFromBottom(distance > NEAR_BOTTOM_PX);
    }
  };

  return (
    <>
      <div
        ref={regionRef}
        className="transcript__scroll"
        tabIndex={0}
        aria-label="Call transcript"
        onScroll={handleScroll}
      >
        {children}
      </div>
      {isAwayFromBottom ? (
        <JumpToLatest
          onJump={() => {
            setIsAwayFromBottom(false);
          }}
        />
      ) : null}
    </>
  );
}

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

export function Transcript({ view }: { view: CallView }) {
  const currentId = latestKenjiLineId(view);
  const startedAt = view.startedAt;
  return (
    <section className="transcript" aria-label="Call transcript">
      <ScrollRegion
        contentKey={
          view.lines.length + Object.keys(view.subtitles).length + (view.partial?.ja.length ?? 0)
        }
      >
        <ol className="transcript__log" role="log" aria-live="polite" aria-relevant="additions">
          {view.lines.map((line) => (
            <TranscriptLine
              key={line.lineId}
              line={line}
              offsetMs={startedAt ? elapsedMs(startedAt, line.at) : 0}
              subtitle={view.subtitles[line.lineId]}
              isCurrent={line.lineId === currentId}
            />
          ))}
        </ol>
        {view.status === "live" ? <ListeningRow text={view.partial?.ja ?? null} /> : null}
      </ScrollRegion>
    </section>
  );
}
