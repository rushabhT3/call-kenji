import type { CallView } from "../call/callView.ts";
import type { BrowserCall } from "../call/useBrowserCall.ts";
import { formatClock } from "../format.ts";
import { SiteHeader } from "../landing/SiteHeader.tsx";
import { Button } from "../ui/Button.tsx";
import { Pill } from "../ui/Pill.tsx";

interface LiveHeaderProps {
  view: CallView;
  elapsedMs: number;
  isDemo: boolean;
  call: BrowserCall | null;
}

function Status({ view, elapsedMs }: Pick<LiveHeaderProps, "view" | "elapsedMs">) {
  const clock = <time className="metric-sm">{formatClock(elapsedMs)}</time>;
  if (view.status === "ended") {
    return <span className="live-status">Call ended · {clock}</span>;
  }
  const channel = view.transport === "phone" ? "Phone call" : "Browser call";
  return (
    <span className="live-status">
      <span className="live-status__dot" aria-hidden="true" />
      <span className="caption live-status__live">Live</span>
      {clock}
      <span className="live-status__channel">{channel}</span>
    </span>
  );
}

function Controls({ call }: { call: BrowserCall }) {
  return (
    <span className="live-controls">
      <Button icon="mic" aria-pressed={call.isMuted} onClick={call.toggleMute}>
        {call.isMuted ? "Unmute" : "Mute"}
      </Button>
      <Button variant="danger" icon="end" onClick={() => void call.end()}>
        End call
      </Button>
    </span>
  );
}

export function LiveHeader({ view, elapsedMs, isDemo, call }: LiveHeaderProps) {
  const canControl = call?.state === "connected" && view.status === "live";
  return (
    <SiteHeader isLive centre={<Status view={view} elapsedMs={elapsedMs} />}>
      {isDemo ? <Pill tone="info" label="Demo replay · 再生" /> : null}
      {canControl ? <Controls call={call} /> : null}
    </SiteHeader>
  );
}
