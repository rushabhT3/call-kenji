import { XRAY_CALLOUTS, XRAY_DESKTOP, type XrayCallout } from "../showcase/content.ts";
import type { FocusId } from "./stops.ts";

const INSETS: readonly FocusId[] = ["turn", "strategist", "compliance"];

function calloutFor(id: FocusId): XrayCallout {
  const callout = XRAY_CALLOUTS.find((candidate) => candidate.id === id);
  if (!callout) {
    throw new Error(`No X-ray callout for ${id}`);
  }
  return callout;
}

function Inset({ id }: { id: FocusId }) {
  const callout = calloutFor(id);
  return (
    <figure className={`xray-inset xray-inset--${id}`} data-focus={id}>
      <figcaption>
        <span className="comic-label">
          {callout.title} · <span lang="ja">{callout.ja}</span>
        </span>
        <span className="xray-inset__text">{callout.text}</span>
      </figcaption>
      <img
        className="xray-inset__shot"
        src={callout.shot.src}
        width={callout.shot.width}
        height={callout.shot.height}
        alt={callout.shot.alt}
        decoding="async"
      />
    </figure>
  );
}

export function XrayStop() {
  return (
    <div className="stop-body xray-wall">
      <figure className="xray-wall__screen">
        <img
          src={XRAY_DESKTOP.src}
          width={XRAY_DESKTOP.width}
          height={XRAY_DESKTOP.height}
          alt={XRAY_DESKTOP.alt}
          decoding="async"
        />
        <figcaption className="stop-lead">
          Most voice demos are a black box. This one shows what Kenji heard, why he answered when he
          did, what his second model advised and which rules held, while the call is still going.
        </figcaption>
      </figure>
      {INSETS.map((id) => (
        <Inset key={id} id={id} />
      ))}
    </div>
  );
}
