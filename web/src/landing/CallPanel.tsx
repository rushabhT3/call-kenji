import type { BrowserCallState } from "../call/useBrowserCall.ts";
import { Button } from "../ui/Button.tsx";
import { ButtonLink } from "../ui/ButtonLink.tsx";
import type { IconName } from "../ui/Icon.tsx";
import { LinkCode } from "./LinkCode.tsx";
import type { ServerReadiness } from "./readiness.ts";
import { useHasWaited } from "./useHasWaited.ts";

/** A warm server answers in well under this; only a sleeping one earns the explanation. */
const WAKING_NOTE_DELAY_MS = 2000;
const WAKING_NOTE =
  "He sleeps when nobody is calling, so the first call of the day takes 10 to 15 seconds to wake him.";
const UNREACHABLE_NOTE = "Kenji's server isn't answering. Reload the page to try again.";

interface CallButtonLook {
  label: string;
  icon: IconName;
  isBusy: boolean;
  isAvailable: boolean;
}

function callButtonLook(readiness: ServerReadiness, callState: BrowserCallState): CallButtonLook {
  if (callState === "connecting") {
    return { label: "Connecting…", icon: "phone", isBusy: true, isAvailable: false };
  }
  if (readiness === "waking") {
    return { label: "Waking Kenji up…", icon: "clock", isBusy: true, isAvailable: false };
  }
  return {
    label: "Call from browser",
    icon: "phone",
    isBusy: false,
    isAvailable: readiness === "ready",
  };
}

interface CallPanelProps {
  phoneNumber: string | null;
  code: string | null;
  callState: BrowserCallState;
  callError: string | null;
  readiness: ServerReadiness;
  onCall: () => void;
  /** The dev softphone, offered only to a browser on the voice server's own machine. */
  softphoneUrl?: string | null | undefined;
}

function PhoneNumber({ phoneNumber }: { phoneNumber: string | null }) {
  if (phoneNumber === null) {
    return <p className="call-panel__number call-panel__number--soon">Phone line opening soon</p>;
  }
  return (
    <a className="call-panel__number numeric" href={`tel:${phoneNumber.replaceAll(" ", "")}`}>
      {phoneNumber}
    </a>
  );
}

function SoftphoneLink({ url }: { url: string }) {
  return (
    <div className="call-panel__softphone">
      <ButtonLink href={url} target="_blank" rel="noopener">
        Call through the phone line (Twilio)
      </ButtonLink>
      <p className="call-panel__note">
        Rings Kenji through Twilio&apos;s network, the way a phone would. On this machine only.
      </p>
    </div>
  );
}

function CallButton({
  readiness,
  callState,
  onCall,
}: Omit<CallPanelProps, "phoneNumber" | "code" | "callError">) {
  const look = callButtonLook(readiness, callState);
  const hasWaited = useHasWaited(readiness === "waking", WAKING_NOTE_DELAY_MS);
  return (
    <>
      <Button
        variant="primary"
        size="lg"
        icon={look.icon}
        isWide
        isBusy={look.isBusy}
        aria-disabled={!look.isAvailable}
        onClick={look.isAvailable ? onCall : undefined}
      >
        {look.label}
      </Button>
      <p className="call-panel__note" aria-live="polite">
        {hasWaited ? WAKING_NOTE : null}
      </p>
      {readiness === "unreachable" ? <p className="call-panel__error">{UNREACHABLE_NOTE}</p> : null}
    </>
  );
}

export function CallPanel(props: CallPanelProps) {
  return (
    <section id="call" className="call-panel" aria-labelledby="call-title">
      <h2 id="call-title" className="caption call-panel__caption">
        Call Kenji · <span lang="ja">ケンジに電話</span>
      </h2>
      <PhoneNumber phoneNumber={props.phoneNumber} />
      <p className="call-panel__note">
        Calls are kept as a text transcript for 30 days, then deleted. Audio is never stored. The
        language model provider may use the text to improve its models, so please don&apos;t share
        real personal details.
      </p>
      <p className="caption call-panel__or">or</p>
      <CallButton readiness={props.readiness} callState={props.callState} onCall={props.onCall} />
      {props.callError ? <p className="call-panel__error">{props.callError}</p> : null}
      {props.softphoneUrl ? <SoftphoneLink url={props.softphoneUrl} /> : null}
      <LinkCode code={props.code} />
    </section>
  );
}
