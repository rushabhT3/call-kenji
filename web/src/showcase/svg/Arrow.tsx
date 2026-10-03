interface ArrowProps {
  d: string;
  /** The id of the figure's arrowhead marker. */
  markerId: string;
  isDashed?: boolean;
  hasHead?: boolean;
}

/** A hand-drawn connector the page can draw on scroll (the diagram-draw hook). */
export function Arrow({ d, markerId, isDashed = false, hasHead = true }: ArrowProps) {
  return (
    <path
      d={d}
      className={
        isDashed
          ? "diagram-draw diagram__arrow diagram__arrow--dashed"
          : "diagram-draw diagram__arrow"
      }
      markerEnd={hasHead ? `url(#${markerId})` : undefined}
    />
  );
}
