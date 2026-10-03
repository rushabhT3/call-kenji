import { Arrow } from "./svg/Arrow.tsx";
import { DiagramFigure } from "./svg/DiagramFigure.tsx";
import { LabelledBox, type LabelledBoxProps } from "./svg/LabelledBox.tsx";
import { arrowheadId, bowedPath, elbowPath, type Point } from "./svg/layout.ts";
import { ShadowBox, type BoxGeometry } from "./svg/ShadowBox.tsx";
import { TextLines, type TextLine } from "./svg/TextLines.tsx";

const ID = "turn-flow";
const WIDTH = 340;
const HEIGHT = 742;
const MARKER = arrowheadId(ID);

const FULL = { x: 16, width: 308 } as const;
const MAIN = { x: 16, width: 168 } as const;
const SIDE = { x: 214, width: 110 } as const;
const MAIN_CENTRE = MAIN.x + MAIN.width / 2;
const SIDE_CENTRE = SIDE.x + SIDE.width / 2;
const START_WIDTH = 130;
const DECISION_HEIGHT = 62;
const ANSWER_LABEL_RISE = 7;
const ANSWER_LABEL_GAP = 6;

type FlowNode = LabelledBoxProps;

const START: FlowNode = {
  step: 1,
  x: MAIN_CENTRE - START_WIDTH / 2,
  y: 82,
  width: START_WIDTH,
  height: 34,
  title: ["You speak"],
  shape: "pill",
  tone: "paper",
};
const HEARD: FlowNode = {
  step: 2,
  ...FULL,
  y: 134,
  height: 52,
  title: ["Silero VAD hears you start"],
  detail: ["so Kenji can be interrupted at once"],
};
const PROPOSED: FlowNode = {
  step: 3,
  ...FULL,
  y: 204,
  height: 52,
  title: ["Soniox proposes the turn is over"],
  detail: ["words + intonation, not a silence timer"],
};
const END: FlowNode = {
  step: 10,
  ...MAIN,
  y: 534,
  height: 54,
  title: ["Turn over:", "Kenji answers"],
  tone: "orange",
  shadow: "red",
};

interface Check {
  question: FlowNode;
  wait: FlowNode;
}

function check(
  step: number,
  y: number,
  question: Omit<FlowNode, keyof BoxGeometry | "step">,
  wait: readonly TextLine[][],
): Check {
  const [title = [], detail = []] = wait;
  return {
    question: { ...question, step, ...MAIN, y, height: DECISION_HEIGHT, shape: "hex" },
    wait: { step: step + 1, ...SIDE, y, height: DECISION_HEIGHT, title, detail, tone: "teal" },
  };
}

const CHECKS: readonly Check[] = [
  check(4, 276, { title: ["Holding?"], detail: ["the Hold button is on"] }, [
    ["Wait until"],
    ["you press Done"],
  ]),
  check(
    6,
    360,
    {
      title: ["On a particle?"],
      detail: [[{ text: "words stop on " }, { text: "は、", lang: "ja" }], "or a filler"],
    },
    [["Wait 2 s"], ["longer"]],
  ),
  check(8, 444, { title: ["Still talking?"], detail: ["Smart Turn v3 hears", "≤ 50% finished"] }, [
    ["Wait 1.5 s"],
    ["longer"],
  ]),
];

const NODES: readonly FlowNode[] = [
  START,
  HEARD,
  PROPOSED,
  ...CHECKS.flatMap((row) => [row.question, row.wait]),
  END,
];

function bottom(node: BoxGeometry): number {
  return node.y + node.height;
}

function middle(node: BoxGeometry): number {
  return node.y + node.height / 2;
}

function down(from: BoxGeometry, to: BoxGeometry, x = MAIN_CENTRE): string {
  return bowedPath({ x, y: bottom(from) }, { x, y: to.y });
}

function Node({ node }: { node: FlowNode }) {
  return <LabelledBox {...node} />;
}

function AnswerLabel({ at, text }: { at: Point; text: string }) {
  return <TextLines x={at.x} y={at.y} lines={[text]} variant="small" anchor="middle" hasHalo />;
}

function CheckLinks({ row, next }: { row: Check; next: BoxGeometry }) {
  const y = middle(row.question);
  const yesStart = MAIN.x + MAIN.width;
  return (
    <>
      <Arrow d={bowedPath({ x: yesStart, y }, { x: SIDE.x, y }, 0)} markerId={MARKER} />
      <AnswerLabel at={{ x: (yesStart + SIDE.x) / 2, y: y - ANSWER_LABEL_RISE }} text="yes" />
      <Arrow d={down(row.question, next)} markerId={MARKER} />
      <AnswerLabel
        at={{ x: MAIN_CENTRE + ANSWER_LABEL_GAP * 3, y: (bottom(row.question) + next.y) / 2 }}
        text="no"
      />
    </>
  );
}

function WaitsEnd() {
  const waits = CHECKS.map((row) => row.wait);
  const last = waits[waits.length - 1] ?? END;
  return (
    <>
      {waits.slice(0, -1).map((wait, index) => (
        <Arrow
          key={wait.step}
          d={down(wait, waits[index + 1] ?? END, SIDE_CENTRE)}
          markerId={MARKER}
          isDashed
          hasHead={false}
        />
      ))}
      <Arrow
        d={elbowPath([
          { x: SIDE_CENTRE, y: bottom(last) },
          { x: SIDE_CENTRE, y: middle(END) },
          { x: MAIN.x + MAIN.width + ANSWER_LABEL_GAP, y: middle(END) },
        ])}
        markerId={MARKER}
        isDashed
      />
    </>
  );
}

const RESUME_NOTE_Y = 612;
const BUBBLE = { ...FULL, y: 650, height: 72 } as const;
const BUBBLE_TAIL_X = [44, 54, 68] as const;
const BUBBLE_TAIL_RISE = 19;
const BUBBLE_TAIL_OVERLAP = 1.5;
const BUBBLE_TAIL = `M ${String(BUBBLE_TAIL_X[0])} ${String(BUBBLE.y + BUBBLE_TAIL_OVERLAP)} L ${String(BUBBLE_TAIL_X[1])} ${String(BUBBLE.y - BUBBLE_TAIL_RISE)} L ${String(BUBBLE_TAIL_X[2])} ${String(BUBBLE.y + BUBBLE_TAIL_OVERLAP)}`;
const BUBBLE_TITLE_DROP = 24;
const BUBBLE_DETAIL_DROP = 44;

function ResumeNote() {
  return (
    <g className="diagram-step" data-step={11}>
      <TextLines
        x={FULL.x + FULL.width / 2}
        y={RESUME_NOTE_Y}
        lines={["Words that resume during a wait", "join the same turn."]}
        variant="note"
        anchor="middle"
      />
    </g>
  );
}

function OverKenjiBubble() {
  const centre = BUBBLE.x + BUBBLE.width / 2;
  return (
    <g className="diagram-step" data-step={12}>
      <ShadowBox {...BUBBLE} />
      <path d={BUBBLE_TAIL} className="diagram__box diagram__box--white" />
      <TextLines
        x={centre}
        y={BUBBLE.y + BUBBLE_TITLE_DROP}
        lines={["Talking over Kenji"]}
        variant="label"
        anchor="middle"
      />
      <TextLines
        x={centre}
        y={BUBBLE.y + BUBBLE_DETAIL_DROP}
        lines={[
          [{ text: "はい", lang: "ja" }, { text: " while he talks → he keeps going." }],
          [{ text: "ちょっと待って", lang: "ja" }, { text: " → he stops." }],
        ]}
        variant="note"
        anchor="middle"
      />
    </g>
  );
}

/** How Kenji decides a caller has finished: Soniox's words, Smart Turn's voice, a particle rule and Hold. */
export function TurnFlow() {
  const firstQuestion = CHECKS[0]?.question ?? END;
  return (
    <DiagramFigure
      id={ID}
      modifier="turns"
      width={WIDTH}
      height={HEIGHT}
      title="When have you finished talking?"
      description="A flowchart. You speak, and Silero VAD hears you start, so Kenji can be interrupted at once. Soniox proposes that the turn is over from the words and intonation, not a silence timer. Three checks follow. If you are holding with the Hold button, Kenji waits until you press Done. If your words stop on a particle such as は or on a filler, he waits 2 seconds longer. If Smart Turn v3 hears your voice still going, 50% finished or less, he waits 1.5 seconds longer. Otherwise, and after any wait, the turn is over and Kenji answers. Words that resume during a wait join the same turn. While Kenji talks, はい lets him keep going and ちょっと待って stops him."
      heading={["When have you finished", "talking?"]}
      headingWidth={228}
      caption="Soniox decides from the words, Smart Turn from the voice, and a Japanese particle rule from the grammar. The Hold button beats all three."
    >
      {NODES.map((node) => (
        <Node key={node.step} node={node} />
      ))}
      <Arrow d={down(START, HEARD)} markerId={MARKER} />
      <Arrow d={down(HEARD, PROPOSED)} markerId={MARKER} />
      <Arrow d={down(PROPOSED, firstQuestion)} markerId={MARKER} />
      {CHECKS.map((row, index) => (
        <CheckLinks key={row.question.step} row={row} next={CHECKS[index + 1]?.question ?? END} />
      ))}
      <WaitsEnd />
      <ResumeNote />
      <OverKenjiBubble />
    </DiagramFigure>
  );
}
