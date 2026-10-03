import type { ReactNode } from "react";
import { arrowheadId, LINE_HEIGHT } from "./layout.ts";
import { TextLines, type TextLine } from "./TextLines.tsx";

interface DiagramFigureProps {
  id: string;
  modifier: "latency" | "turns" | "pipeline";
  width: number;
  height: number;
  /** The accessible name; `description` is the full text alternative. */
  title: string;
  description: string;
  /** The title as lettered in the narration box at the top left. */
  heading: readonly TextLine[];
  headingWidth: number;
  caption: ReactNode;
  defs?: ReactNode;
  children: ReactNode;
}

const PANEL_INSET = 3;
const PANEL_SHADOW = 6;
const PANEL_RADIUS = 16;
const NARRATION_INSET = 14;
const NARRATION_PADDING = 10;
const NARRATION_CAP = 12;

function Panel({ width, height }: { width: number; height: number }) {
  const size = {
    width: width - PANEL_INSET * 2 - PANEL_SHADOW,
    height: height - PANEL_INSET * 2 - PANEL_SHADOW,
  };
  return (
    <>
      <rect
        {...size}
        x={PANEL_INSET + PANEL_SHADOW}
        y={PANEL_INSET + PANEL_SHADOW}
        rx={PANEL_RADIUS}
        className="diagram__shadow diagram__shadow--red"
      />
      <rect
        {...size}
        x={PANEL_INSET}
        y={PANEL_INSET}
        rx={PANEL_RADIUS}
        className="diagram__panel"
      />
    </>
  );
}

function Narration({ lines, width }: { lines: readonly TextLine[]; width: number }) {
  const height = NARRATION_PADDING * 2 + NARRATION_CAP + (lines.length - 1) * LINE_HEIGHT.title;
  return (
    <g className="diagram-step" data-step={0}>
      <rect
        x={NARRATION_INSET}
        y={NARRATION_INSET}
        width={width}
        height={height}
        className="diagram__narration"
      />
      <TextLines
        x={NARRATION_INSET + NARRATION_PADDING}
        y={NARRATION_INSET + NARRATION_PADDING + NARRATION_CAP}
        lines={lines}
        variant="title"
      />
    </g>
  );
}

/** A diagram drawn as one comic panel: frame, narration box, content and a caption below. */
export function DiagramFigure(props: DiagramFigureProps) {
  const { id, width, height } = props;
  return (
    <figure className="comic-figure">
      <svg
        viewBox={`0 0 ${String(width)} ${String(height)}`}
        className={`diagram diagram--${props.modifier}`}
        role="img"
        aria-labelledby={`${id}-title ${id}-desc`}
      >
        <title id={`${id}-title`}>{props.title}</title>
        <desc id={`${id}-desc`}>{props.description}</desc>
        <defs>
          <marker
            id={arrowheadId(id)}
            viewBox="0 0 10 10"
            refX="8"
            refY="5"
            markerWidth="5"
            markerHeight="5"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" className="diagram__arrowhead" />
          </marker>
          {props.defs}
        </defs>
        <Panel width={width} height={height} />
        <Narration lines={props.heading} width={props.headingWidth} />
        {props.children}
      </svg>
      <figcaption>{props.caption}</figcaption>
    </figure>
  );
}
