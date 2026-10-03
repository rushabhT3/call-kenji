import { centredBaselines, type TextVariant } from "./layout.ts";
import {
  ShadowBox,
  type BoxGeometry,
  type BoxShadow,
  type BoxShape,
  type BoxTone,
} from "./ShadowBox.tsx";
import { TextLines, type TextLine } from "./TextLines.tsx";

export interface LabelledBoxProps extends BoxGeometry {
  /** Order in which the page reveals this node (see the diagram-step hook in diagrams.css). */
  step: number;
  title: readonly TextLine[];
  detail?: readonly TextLine[];
  detailVariant?: TextVariant;
  shape?: BoxShape;
  tone?: BoxTone;
  shadow?: BoxShadow;
}

/** A diagram node: its frame, a marker-lettered title and optional small print, centred. */
export function LabelledBox({
  step,
  title,
  detail = [],
  detailVariant = "note",
  shape = "rect",
  tone = "white",
  shadow = "ink",
  ...box
}: LabelledBoxProps) {
  const centre = box.x + box.width / 2;
  const baselines = centredBaselines(box.y, box.height, {
    title: title.length,
    detail: detail.length,
    detailVariant,
  });
  return (
    <g className="diagram-step" data-step={step}>
      <ShadowBox {...box} shape={shape} tone={tone} shadow={shadow} />
      <TextLines x={centre} y={baselines.title} lines={title} variant="label" anchor="middle" />
      {detail.length > 0 ? (
        <TextLines
          x={centre}
          y={baselines.detail}
          lines={detail}
          variant={detailVariant}
          anchor="middle"
        />
      ) : null}
    </g>
  );
}
