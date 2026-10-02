import type { ReactNode } from "react";

interface SiteHeaderProps {
  isLive?: boolean;
  centre?: ReactNode;
  children?: ReactNode;
}

export function SiteHeader({ isLive = false, centre, children }: SiteHeaderProps) {
  return (
    <header className={isLive ? "site-header site-header--live" : "site-header"}>
      <div className="site-header__bar">
        <p className="site-header__brand">
          <span className="site-header__wordmark">
            <span className="site-header__long">Minato Servicer · </span>
            <span className="site-header__short">Minato · </span>
            <span lang="ja">
              みなと
              <span className="site-header__ja-full">債権回収</span>
            </span>
          </span>
          <span className="caption site-header__note">Demo · fictional company</span>
        </p>
        {centre ? <div className="site-header__centre">{centre}</div> : null}
        <div className="site-header__extra">{children}</div>
      </div>
    </header>
  );
}
