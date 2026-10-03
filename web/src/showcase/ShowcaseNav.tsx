export function ShowcaseNav() {
  return (
    <header className="showcase-nav">
      <div className="showcase__container showcase-nav__bar">
        <a className="showcase-nav__home" href="/">
          Call Kenji
          <span className="visually-hidden">, home</span>
        </a>
        <nav className="showcase-nav__links" aria-label="Pages">
          <a className="showcase-nav__link" href="/?demo=1">
            Demo
          </a>
          <a className="showcase-nav__link" href="/#call">
            Call him
          </a>
        </nav>
      </div>
    </header>
  );
}
