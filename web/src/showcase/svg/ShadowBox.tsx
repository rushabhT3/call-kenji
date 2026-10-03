export type BoxShape = "rect" | "pill" | "hex";
export type BoxTone = "white" | "paper" | "orange" | "green" | "blue" | "teal";
export type BoxShadow = "ink" | "red" | "none";

export interface BoxGeometry {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface ShadowBoxProps extends BoxGeometry {
  shape?: BoxShape;
  tone?: BoxTone;
  shadow?: BoxShadow;
}

const SHADOW_OFFSET = 4;
const CORNER_RADIUS = 10;
const HEX_TIP = 14;

function hexPoints({ x, y, width, height }: BoxGeometry): string {
  const middle = y + height / 2;
  return [
    [x + HEX_TIP, y],
    [x + width - HEX_TIP, y],
    [x + width, middle],
    [x + width - HEX_TIP, y + height],
    [x + HEX_TIP, y + height],
    [x, middle],
  ]
    .map((point) => point.join(","))
    .join(" ");
}

function Shape({ shape, className, ...box }: BoxGeometry & { shape: BoxShape; className: string }) {
  if (shape === "hex") {
    return <polygon points={hexPoints(box)} className={className} />;
  }
  const radius = shape === "pill" ? box.height / 2 : CORNER_RADIUS;
  return <rect {...box} rx={radius} className={className} />;
}

/** A comic frame: a white (or coloured) shape over a hard offset shadow. */
export function ShadowBox({
  shape = "rect",
  tone = "white",
  shadow = "ink",
  ...box
}: ShadowBoxProps) {
  return (
    <>
      {shadow === "none" ? null : (
        <Shape
          shape={shape}
          x={box.x + SHADOW_OFFSET}
          y={box.y + SHADOW_OFFSET}
          width={box.width}
          height={box.height}
          className={`diagram__shadow diagram__shadow--${shadow}`}
        />
      )}
      <Shape shape={shape} {...box} className={`diagram__box diagram__box--${tone}`} />
    </>
  );
}
