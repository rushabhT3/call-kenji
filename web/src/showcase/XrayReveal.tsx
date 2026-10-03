import { XRAY_CALLOUTS, XRAY_DESKTOP, XRAY_PHONE, type XrayCallout } from "./content.ts";

const PHONE_QUERY = "(max-width: 767px)";

function Screen() {
  return (
    <div className="xray-reveal__screen">
      <div className="xray-reveal__chrome" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      <picture>
        <source
          media={PHONE_QUERY}
          srcSet={XRAY_PHONE.src}
          width={XRAY_PHONE.width}
          height={XRAY_PHONE.height}
        />
        <img
          className="xray-reveal__shot"
          src={XRAY_DESKTOP.src}
          width={XRAY_DESKTOP.width}
          height={XRAY_DESKTOP.height}
          alt={XRAY_DESKTOP.alt}
          loading="lazy"
          decoding="async"
        />
      </picture>
    </div>
  );
}

function Callout({ callout, index }: { callout: XrayCallout; index: number }) {
  return (
    <li className="xray-callout comic-panel">
      <p className="comic-label">
        {String(index + 1).padStart(2, "0")} · <span lang="ja">{callout.ja}</span>
      </p>
      <h3 className="xray-callout__title">{callout.title}</h3>
      <p className="xray-callout__text">{callout.text}</p>
      <img
        className="xray-callout__shot"
        src={callout.shot.src}
        width={callout.shot.width}
        height={callout.shot.height}
        alt={callout.shot.alt}
        loading="lazy"
        decoding="async"
      />
    </li>
  );
}

export function XrayReveal() {
  return (
    <section className="xray-reveal" aria-labelledby="xray-reveal-title">
      <div className="showcase__container xray-reveal__intro">
        <p className="comic-label">The X-ray</p>
        <h2 id="xray-reveal-title" className="showcase-heading">
          Watch him think. Live.
        </h2>
        <p className="showcase-lead">
          Most voice demos are a black box. Kenji's X-ray shows what he heard, why he answered when
          he did, what his second model advised and which rules held, while the call is still going.
          These are real screenshots from a recorded call.
        </p>
      </div>
      <div className="showcase__container xray-reveal__stage">
        <Screen />
        <ol className="xray-reveal__callouts">
          {XRAY_CALLOUTS.map((callout, index) => (
            <Callout key={callout.id} callout={callout} index={index} />
          ))}
        </ol>
      </div>
    </section>
  );
}
