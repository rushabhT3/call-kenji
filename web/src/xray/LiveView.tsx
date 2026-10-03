import { PostCall } from "../aftercall/PostCall.tsx";
import { finishedCallMs, latestCallerTone, type CallView } from "../call/callView.ts";
import type { BrowserCall } from "../call/useBrowserCall.ts";
import type { Persona } from "../contract/personas.ts";
import type { Loadable } from "../persona/catalog.ts";
import { Button } from "../ui/Button.tsx";
import { ComplianceCard } from "./ComplianceCard.tsx";
import { DemoBanner } from "./DemoBanner.tsx";
import { HoldButton } from "./HoldButton.tsx";
import { LatencyCard } from "./LatencyCard.tsx";
import { LiveHeader } from "./LiveHeader.tsx";
import { NowStrip } from "./NowStrip.tsx";
import { PersonaCard } from "./PersonaCard.tsx";
import { StrategistCard } from "./StrategistCard.tsx";
import { SummaryChips } from "./SummaryChips.tsx";
import { Transcript } from "./Transcript.tsx";
import { TurnCard } from "./TurnCard.tsx";
import { useCallTimer } from "./useCallTimer.ts";

interface LiveViewProps {
  view: CallView;
  isDemo: boolean;
  call: BrowserCall | null;
  isFeedLost: boolean;
  startedAtMs: number | null;
  endedAtMs: number | null;
  /** Who the caller plays on this call. */
  persona: Loadable<Persona>;
}

function liveClasses(status: CallView["status"], hasCallBar: boolean): string {
  const classes = [
    "container",
    "live",
    hasCallBar ? "live--with-bar" : "",
    status === "ended" ? "live--ended" : "",
  ];
  return classes.filter(Boolean).join(" ");
}

function Rail({ view }: { view: CallView }) {
  return (
    <div className="rail">
      <TurnCard turn={view.turn} turnEnd={view.turnEnd} />
      <StrategistCard
        advice={view.strategist}
        identityGate={view.compliance?.identity_gate ?? null}
        callerTone={latestCallerTone(view)}
      />
      <ComplianceCard compliance={view.compliance} />
      <LatencyCard turns={view.latency} />
    </div>
  );
}

function MobileCallBar({ call }: { call: BrowserCall }) {
  return (
    <div className="call-bar">
      <Button icon="mic" aria-pressed={call.isMuted} onClick={call.toggleMute}>
        {call.isMuted ? "Unmute" : "Mute"}
      </Button>
      <HoldButton isOnHold={call.isOnHold} onToggle={call.toggleHold} />
      <Button variant="danger" icon="end" onClick={() => void call.end()}>
        End call
      </Button>
    </div>
  );
}

export function LiveView(props: LiveViewProps) {
  const { view, isDemo, call, isFeedLost } = props;
  const timerMs = useCallTimer(props.startedAtMs, props.endedAtMs);
  const elapsedMs = finishedCallMs(view) ?? timerMs;
  const hasCallBar = call?.state === "connected" && view.status === "live";
  return (
    <>
      <LiveHeader view={view} elapsedMs={elapsedMs} isDemo={isDemo} call={call} />
      <main className={liveClasses(view.status, hasCallBar)}>
        {isDemo ? <DemoBanner /> : null}
        {isFeedLost ? (
          <p className="banner" role="alert">
            Connection lost. The call may still be running. Reload to reconnect.
          </p>
        ) : null}
        <div className="live__grid">
          <PersonaCard
            persona={props.persona}
            node={view.node}
            status={view.status}
            speaker={hasCallBar ? { clips: call.clips, isMuted: call.isMuted } : null}
          />
          <div className="live__main">
            <NowStrip view={view} isOnHold={hasCallBar && call.isOnHold} />
            <SummaryChips view={view} />
            <Transcript view={view} />
          </div>
          <Rail view={view} />
        </div>
        {view.status === "ended" ? <PostCall view={view} isDemo={isDemo} /> : null}
      </main>
      {hasCallBar ? <MobileCallBar call={call} /> : null}
    </>
  );
}
