import { LINE_HEIGHT, type TextVariant } from "./layout.ts";

export interface TextSegment {
  text: string;
  lang?: "ja";
}

/** One line of diagram text; Japanese runs are segments marked `lang: "ja"`. */
export type TextLine = string | readonly TextSegment[];

interface TextLinesProps {
  x: number;
  y: number;
  lines: readonly TextLine[];
  variant: TextVariant;
  anchor?: "start" | "middle" | "end";
  /** Outlines the letters in white so a line crossing them cannot hide the text. */
  hasHalo?: boolean;
}

function Segments({ line }: { line: TextLine }) {
  if (typeof line === "string") {
    return line;
  }
  return line.map((segment, index) => (
    <tspan key={index} lang={segment.lang}>
      {segment.text}
    </tspan>
  ));
}

/** Lines of SVG text set one under another from the first baseline. */
export function TextLines({
  x,
  y,
  lines,
  variant,
  anchor = "start",
  hasHalo = false,
}: TextLinesProps) {
  const className = `diagram__text diagram__text--${variant}${hasHalo ? " diagram__text--halo" : ""}`;
  return (
    <text x={x} y={y} className={className} textAnchor={anchor}>
      {lines.map((line, index) => (
        <tspan key={index} x={x} dy={index === 0 ? 0 : LINE_HEIGHT[variant]}>
          <Segments line={line} />
        </tspan>
      ))}
    </text>
  );
}
