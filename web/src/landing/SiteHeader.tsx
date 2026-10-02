import type { ReactNode } from "react";

interface SiteHeaderProps {
  children?: ReactNode;
}

export function SiteHeader({ children }: SiteHeaderProps) {
  return (
    <header className="site-header">
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
        <div className="site-header__extra">{children}</div>
      </div>
    </header>
  );
}
