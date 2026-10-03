import { DEMO_LINK, TRAILER_LINKS } from "./content.ts";

/** Where to go once the credits roll. */
export function TrailerLinks() {
  return (
    <nav className="trailer-links" aria-label="After the trailer">
      <ul className="trailer-links__buttons">
        {TRAILER_LINKS.map((link) => (
          <li key={link.href}>
            <a
              className={link.isPrimary ? "comic-button comic-button--primary" : "comic-button"}
              href={link.href}
            >
              {link.label}
            </a>
          </li>
        ))}
      </ul>
      <a className="trailer-links__demo" href={DEMO_LINK.href}>
        {DEMO_LINK.label}
      </a>
    </nav>
  );
}
