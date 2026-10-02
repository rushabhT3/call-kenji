import type { CSSProperties } from "react";

type Fill = "success" | "danger" | "ink";

interface BudgetBarProps {
  value: number;
  scale: number;
  marker: number;
  markerLabel: string;
  fill: Fill;
  label: string;
}

const percent = (part: number, whole: number) =>
  `${String(Math.max(0, Math.min(100, (part / whole) * 100)))}%`;

export function BudgetBar({ value, scale, marker, markerLabel, fill, label }: BudgetBarProps) {
  const position = { "--value": percent(value, scale), "--marker": percent(marker, scale) };
  return (
    <div className="budget">
      <div
        className="budget__track"
        role="img"
        aria-label={`${label}: ${String(value)}, ${markerLabel}`}
        style={position as CSSProperties}
      >
        <span className={`budget__fill budget__fill--${fill}`} />
        <span className="budget__marker" />
      </div>
      <p className="caption budget__marker-label" aria-hidden="true">
        {markerLabel}
      </p>
    </div>
  );
}
