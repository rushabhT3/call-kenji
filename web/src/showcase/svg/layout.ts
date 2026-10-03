export type TextVariant = "title" | "label" | "note" | "small" | "big";

export interface Point {
  x: number;
  y: number;
}

/** Baseline-to-baseline distance for each text style, in diagram units (see diagrams.css). */
export const LINE_HEIGHT: Record<TextVariant, number> = {
  title: 19,
  label: 18,
  note: 16,
  small: 16,
  big: 30,
};

const CAP_HEIGHT: Record<TextVariant, number> = {
  title: 12,
  label: 11,
  note: 9,
  small: 9,
  big: 19,
};

const DETAIL_GAP = 3;
const DEFAULT_BOW = 6;

export interface TextBlock {
  title: number;
  detail: number;
  detailVariant: TextVariant;
}

/** Where the first title baseline and the first detail baseline sit to centre a block in a box. */
export function centredBaselines(
  top: number,
  height: number,
  block: TextBlock,
): { title: number; detail: number } {
  const titleSpan = CAP_HEIGHT.label + (block.title - 1) * LINE_HEIGHT.label;
  const detailSpan =
    block.detail > 0 ? DETAIL_GAP + block.detail * LINE_HEIGHT[block.detailVariant] : 0;
  const title = top + (height - titleSpan - detailSpan) / 2 + CAP_HEIGHT.label;
  const lastTitle = title + (block.title - 1) * LINE_HEIGHT.label;
  return { title, detail: lastTitle + DETAIL_GAP + LINE_HEIGHT[block.detailVariant] };
}

/** The id of a figure's arrowhead marker; SVG ids are page-wide, so each figure names its own. */
export function arrowheadId(figureId: string): string {
  return `${figureId}-arrowhead`;
}

/** A gently bowed line between two points, so a connector reads as drawn by hand. */
export function bowedPath(from: Point, to: Point, bow = DEFAULT_BOW): string {
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const length = Math.hypot(dx, dy) || 1;
  const controlX = (from.x + to.x) / 2 - (dy / length) * bow;
  const controlY = (from.y + to.y) / 2 + (dx / length) * bow;
  return `M ${String(from.x)} ${String(from.y)} Q ${String(controlX)} ${String(controlY)} ${String(to.x)} ${String(to.y)}`;
}

/** A connector with right-angle turns through each point. */
export function elbowPath(points: readonly Point[]): string {
  return points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${String(point.x)} ${String(point.y)}`)
    .join(" ");
}
