import type { ReactNode } from "react";

interface SiteHeaderProps {
  isLive?: boolean;
  /** Where the company name leads; left out during a call, where a stray click would end it. */
  homeHref?: string | undefined;
  centre?: ReactNode;
  children?: ReactNode;
}

function Wordmark() {
  return (
    <span className="site-header__wordmark">
      <span className="site-header__long">Minato Servicer · </span>
      <span className="site-header__short">Minato · </span>
      <span lang="ja">
        みなと
        <span className="site-header__ja-full">債権回収</span>
      </span>
    </span>
  );
}

export function SiteHeader({ isLive = false, homeHref, centre, children }: SiteHeaderProps) {
  return (
    <header className={isLive ? "site-header site-header--live" : "site-header"}>
      <div className="site-header__bar">
        <p className="site-header__brand">
          {homeHref ? (
            <a className="site-header__home" href={homeHref}>
              <Wordmark />
              <span className="visually-hidden">, home</span>
            </a>
          ) : (
            <Wordmark />
          )}
          <span className="caption site-header__note">Demo · fictional company</span>
        </p>
        {centre ? <div className="site-header__centre">{centre}</div> : null}
        <div className="site-header__extra">{children}</div>
      </div>
    </header>
  );
}
