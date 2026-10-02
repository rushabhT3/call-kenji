import type { BrowserCallState } from "../call/useBrowserCall.ts";
import { Button } from "../ui/Button.tsx";
import { LinkCode } from "./LinkCode.tsx";

interface CallPanelProps {
  phoneNumber: string | null;
  code: string | null;
  callState: BrowserCallState;
  callError: string | null;
  canCall: boolean;
  onCall: () => void;
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

export function CallPanel(props: CallPanelProps) {
  const isConnecting = props.callState === "connecting";
  return (
    <section className="call-panel" aria-labelledby="call-title">
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
      <Button
        variant="primary"
        size="lg"
        icon="phone"
        isWide
        isBusy={isConnecting}
        aria-disabled={!props.canCall || isConnecting}
        onClick={props.canCall && !isConnecting ? props.onCall : undefined}
      >
        {isConnecting ? "Connecting…" : "Call from browser"}
      </Button>
      {props.callError ? <p className="call-panel__error">{props.callError}</p> : null}
      <LinkCode code={props.code} />
    </section>
  );
}
