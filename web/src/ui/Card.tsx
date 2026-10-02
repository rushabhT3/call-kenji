import type { ReactNode } from "react";

interface CardProps {
  id: string;
  title: string;
  titleJa: string;
  summary: string;
  isEmpty?: boolean;
  status?: ReactNode;
  className?: string;
  children?: ReactNode;
}

export function Card({
  id,
  title,
  titleJa,
  summary,
  isEmpty,
  status,
  className,
  children,
}: CardProps) {
  const headingId = `${id}-title`;
  return (
    <section id={id} className={`card ${className ?? ""}`.trim()} aria-labelledby={headingId}>
      <header className="card__header">
        <span className="card__marker" aria-hidden="true" />
        <h2 id={headingId} className="caption card__title">
          {title} · <span lang="ja">{titleJa}</span>
        </h2>
        {status ? <span className="card__status">{status}</span> : null}
      </header>
      <p className={isEmpty ? "card__summary card__summary--empty" : "card__summary"}>{summary}</p>
      {children}
    </section>
  );
}

interface RowProps {
  label: string;
  labelJa?: string;
  isStacked?: boolean;
  children: ReactNode;
}

export function Row({ label, labelJa, isStacked = false, children }: RowProps) {
  return (
    <div className={isStacked ? "row row--stacked" : "row"}>
      <dt className="caption row__label">
        {label}
        {labelJa ? (
          <>
            {" "}
            <span lang="ja">{labelJa}</span>
          </>
        ) : null}
      </dt>
      <dd className="row__value">{children}</dd>
    </div>
  );
}
