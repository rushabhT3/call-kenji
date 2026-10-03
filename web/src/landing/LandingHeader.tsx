import { FeaturesLink } from "./FeaturesLink.tsx";
import { SiteHeader } from "./SiteHeader.tsx";

export function LandingHeader() {
  return (
    <SiteHeader homeHref="/">
      <FeaturesLink />
      <a className="caption site-header__link" href="#how-to-read">
        <span className="site-header__link-long">How to read the X-ray</span>
        <span className="site-header__link-short">How it works</span>
      </a>
      <a className="caption site-header__link" href="/?demo=1">
        <span className="site-header__link-long">Watch a demo call</span>
        <span className="site-header__link-short">Demo</span>
      </a>
    </SiteHeader>
  );
}
