import { SHOWCASE_PATH } from "../showcase/route.ts";
import { SiteHeader } from "./SiteHeader.tsx";

export function LandingHeader() {
  return (
    <SiteHeader homeHref="/">
      <a className="caption site-header__link features-link" href={SHOWCASE_PATH}>
        <span className="features-link__plain" aria-hidden="true">
          Features
        </span>
        <span className="features-link__comic">Features</span>
      </a>
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
