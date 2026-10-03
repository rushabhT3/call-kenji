import { Arrow } from "./svg/Arrow.tsx";
import { DiagramFigure } from "./svg/DiagramFigure.tsx";
import { arrowheadId, bowedPath, LINE_HEIGHT } from "./svg/layout.ts";
import { ShadowBox } from "./svg/ShadowBox.tsx";
import { TextLines, type TextLine } from "./svg/TextLines.tsx";

const ID = "latency-chart";
const WIDTH = 340;
const HATCH_ID = `${ID}-hatch`;

const LAST_SECOND = 6;
const TICK_SECONDS = [0, 1, 2, 3, 4, 5, 6] as const;
const AXIS_START = 30;
const AXIS_END = 306;
const UNITS_PER_SECOND = (AXIS_END - AXIS_START) / LAST_SECOND;

const BUDGET_SECONDS = 1.5;
const FIRST_AUDIO_SECONDS = 0.7;
const ACKNOWLEDGEMENT_END_SECONDS = 1.2;
const MODEL_EARLIEST_SECONDS = 2;

const FIRST_ROW_TOP = 96;
const ROW_STEP = 80;
const LABEL_DROP = 14;
const TRACK_DROP = 22;
const TRACK_HEIGHT = 26;
const TRACK_TEXT_DROP = 18;
const NOTE_DROP = 66;
const BAR_RADIUS = 6;
const TICK_LENGTH = 6;
const TICK_LABEL_DROP = 20;
const BUDGET_LABEL_RISE = 10;
const BUDGET_LABEL_GAP = 6;
const CALLOUT_FIGURE_INSET = 14;
const CALLOUT_FIGURE_DROP = 40;
const CALLOUT_TEXT_X = 150;
const CALLOUT_TEXT_DROP = 19;
const CALLOUT_ARROW_GAP = 10;
const CALLOUT_ARROW_START = 38;
const CALLOUT_ARROW_END = 55;
const CALLOUT_DROP = 42;
const CALLOUT_SIZE = { x: 30, width: 276, height: 58 } as const;
const BOTTOM_MARGIN = 20;

type PieceKind = "silence" | "acknowledgement" | "floor" | "rules" | "model";

interface Piece {
  kind: PieceKind;
  from: number;
  to: number;
  text?: string;
}

interface Row {
  label: string;
  pieces: readonly Piece[];
  note: readonly TextLine[];
}

const ROWS: readonly Row[] = [
  {
    label: "A reasoning model, waited on",
    pieces: [
      { kind: "silence", from: 0, to: MODEL_EARLIEST_SECONDS, text: "silence" },
      { kind: "model", from: MODEL_EARLIEST_SECONDS, to: LAST_SECOND },
    ],
    note: ["Muse Spark answers in 2–6 s"],
  },
  {
    label: "Kenji, when the model is needed",
    pieces: [
      { kind: "silence", from: 0, to: FIRST_AUDIO_SECONDS },
      { kind: "acknowledgement", from: FIRST_AUDIO_SECONDS, to: ACKNOWLEDGEMENT_END_SECONDS },
      { kind: "floor", from: ACKNOWLEDGEMENT_END_SECONDS, to: MODEL_EARLIEST_SECONDS },
      { kind: "model", from: MODEL_EARLIEST_SECONDS, to: LAST_SECOND },
    ],
    note: [
      [{ text: "「はい、」", lang: "ja" }, { text: " at once; he keeps the floor" }],
      "until the model's answer is ready",
    ],
  },
  {
    label: "Kenji, when rules know the answer",
    pieces: [
      { kind: "silence", from: 0, to: FIRST_AUDIO_SECONDS },
      {
        kind: "rules",
        from: FIRST_AUDIO_SECONDS,
        to: LAST_SECOND,
        text: "his answer, no model wait",
      },
    ],
    note: ["identity, an offer, a plain yes"],
  },
];

function at(seconds: number): number {
  return AXIS_START + seconds * UNITS_PER_SECOND;
}

function rowTop(row: number): number {
  return ROWS.slice(0, row).reduce(
    (top, earlier) => top + ROW_STEP + (earlier.note.length - 1) * LINE_HEIGHT.note,
    FIRST_ROW_TOP,
  );
}

const AXIS_Y = rowTop(ROWS.length);
const CALLOUT = { ...CALLOUT_SIZE, y: AXIS_Y + CALLOUT_DROP };
const HEIGHT = CALLOUT.y + CALLOUT.height + BOTTOM_MARGIN;

const BAR_CLASS: Record<Exclude<PieceKind, "floor" | "model">, string> = {
  silence: "diagram__silence",
  acknowledgement: "diagram__box diagram__box--orange",
  rules: "diagram__box diagram__box--green",
};

function Bar({ piece, row }: { piece: Piece; row: number }) {
  const top = rowTop(row) + TRACK_DROP;
  const bar = {
    x: at(piece.from),
    y: top,
    width: at(piece.to) - at(piece.from),
    height: TRACK_HEIGHT,
  };
  if (piece.kind === "floor") {
    const middle = top + TRACK_HEIGHT / 2;
    return (
      <path
        d={`M ${String(bar.x)} ${String(middle)} H ${String(bar.x + bar.width)}`}
        className="diagram-draw diagram__floor"
      />
    );
  }
  if (piece.kind === "model") {
    return (
      <>
        <rect {...bar} rx={BAR_RADIUS} className="latency-bar diagram__band-base" data-row={row} />
        <rect
          {...bar}
          rx={BAR_RADIUS}
          fill={`url(#${HATCH_ID})`}
          className="latency-bar diagram__band"
          data-row={row}
        />
      </>
    );
  }
  return (
    <rect
      {...bar}
      rx={BAR_RADIUS}
      className={`latency-bar ${BAR_CLASS[piece.kind]}`}
      data-row={row}
    />
  );
}

function BarText({ piece, row }: { piece: Piece; row: number }) {
  if (piece.text === undefined) {
    return null;
  }
  const centre = (at(piece.from) + at(piece.to)) / 2;
  return (
    <TextLines
      x={centre}
      y={rowTop(row) + TRACK_DROP + TRACK_TEXT_DROP}
      lines={[piece.text]}
      variant="small"
      anchor="middle"
    />
  );
}

function TimelineRow({ row, index }: { row: Row; index: number }) {
  const top = rowTop(index);
  return (
    <g className="diagram-step" data-step={index + 1}>
      <TextLines x={AXIS_START} y={top + LABEL_DROP} lines={[row.label]} variant="label" hasHalo />
      {row.pieces.map((piece) => (
        <Bar key={piece.kind + String(piece.from)} piece={piece} row={index} />
      ))}
      {row.pieces.map((piece) => (
        <BarText key={piece.kind + String(piece.from)} piece={piece} row={index} />
      ))}
      <TextLines x={AXIS_START} y={top + NOTE_DROP} lines={row.note} variant="note" hasHalo />
    </g>
  );
}

function Axis() {
  return (
    <>
      <path
        d={`M ${String(AXIS_START)} ${String(AXIS_Y)} H ${String(AXIS_END)}`}
        className="diagram-draw diagram__axis"
      />
      {TICK_SECONDS.map((second) => (
        <g key={second}>
          <path
            d={`M ${String(at(second))} ${String(AXIS_Y)} v ${String(TICK_LENGTH)}`}
            className="diagram__axis"
          />
          <TextLines
            x={at(second)}
            y={AXIS_Y + TICK_LABEL_DROP}
            lines={[`${String(second)} s`]}
            variant="small"
            anchor="middle"
          />
        </g>
      ))}
    </>
  );
}

function Budget() {
  const x = at(BUDGET_SECONDS);
  return (
    <>
      <path
        d={`M ${String(x)} ${String(FIRST_ROW_TOP)} V ${String(AXIS_Y)}`}
        className="diagram-draw diagram__budget"
      />
      <TextLines
        x={x + BUDGET_LABEL_GAP}
        y={FIRST_ROW_TOP - BUDGET_LABEL_RISE}
        lines={["1.5 s budget"]}
        variant="small"
      />
    </>
  );
}

function FirstAudioCallout() {
  const x = at(FIRST_AUDIO_SECONDS);
  return (
    <g className="latency-callout">
      <path
        d={`M ${String(x)} ${String(rowTop(1) + TRACK_DROP)} V ${String(AXIS_Y)}`}
        className="diagram__guide"
      />
      <Arrow
        d={bowedPath(
          { x: CALLOUT_ARROW_START, y: CALLOUT.y },
          { x: CALLOUT_ARROW_END, y: AXIS_Y + CALLOUT_ARROW_GAP },
        )}
        markerId={arrowheadId(ID)}
      />
      <ShadowBox {...CALLOUT} shadow="red" />
      <TextLines
        x={CALLOUT.x + CALLOUT_FIGURE_INSET}
        y={CALLOUT.y + CALLOUT_FIGURE_DROP}
        lines={["≈0.7 s"]}
        variant="big"
      />
      <TextLines
        x={CALLOUT_TEXT_X}
        y={CALLOUT.y + CALLOUT_TEXT_DROP}
        lines={["to Kenji's first audio,", "p50, measured", "on the server"]}
        variant="note"
      />
    </g>
  );
}

function Hatch() {
  return (
    <pattern
      id={HATCH_ID}
      width="7"
      height="7"
      patternUnits="userSpaceOnUse"
      patternTransform="rotate(45)"
    >
      <path d="M 0 0 V 7" className="diagram__hatch" />
    </pattern>
  );
}

/** Three timelines of the silence after a caller stops: a model waited on, and Kenji's two paths. */
export function LatencyChart() {
  return (
    <DiagramFigure
      id={ID}
      modifier="latency"
      width={WIDTH}
      height={HEIGHT}
      title="What you hear after you stop talking"
      description="A timeline from the moment you stop talking, 0 to 6 seconds, with Kenji's 1.5 second budget marked. A reasoning model that is waited on leaves silence until its answer lands somewhere between 2 and 6 seconds. When Kenji needs the model, he says はい at about 0.7 seconds and keeps the floor until the model's answer is ready, between 2 and 6 seconds. When rules know the answer, such as an identity check, an offer or a plain yes, his full answer starts at about 0.7 seconds with no model wait. About 0.7 seconds is the median time to Kenji's first audio on real voice calls, measured on the server."
      heading={["What you hear after", "you stop talking"]}
      headingWidth={206}
      defs={<Hatch />}
      caption={
        <>
          p50 on real voice calls. Rules answer predictable turns; every other turn opens with{" "}
          <span lang="ja">「はい、」</span> while the model thinks, and a request that has not
          streamed after 2.5 s is raced by a second one.
        </>
      }
    >
      <Budget />
      {ROWS.map((row, index) => (
        <TimelineRow key={row.label} row={row} index={index} />
      ))}
      <Axis />
      <FirstAudioCallout />
    </DiagramFigure>
  );
}
