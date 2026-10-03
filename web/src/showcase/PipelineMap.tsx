import {
  AUDIT,
  BROWSER,
  BROWSER_AUDIO_X,
  DOMAIN,
  EVENTS,
  FAST_PATH,
  FRAME,
  HEARING,
  HEIGHT,
  INNER,
  KANA,
  PHONE,
  RETURN_X,
  SIDE_LABEL_Y,
  SIDE_LANE,
  SIDE_RAIL_X,
  SPEECH_INSET,
  TALKER,
  TURNS,
  VOICE,
  WORKER,
} from "./pipelineLayout.ts";
import { Arrow } from "./svg/Arrow.tsx";
import { DiagramFigure } from "./svg/DiagramFigure.tsx";
import { LabelledBox, type LabelledBoxProps } from "./svg/LabelledBox.tsx";
import { arrowheadId, bowedPath, elbowPath, type Point } from "./svg/layout.ts";
import type { BoxGeometry } from "./svg/ShadowBox.tsx";
import { TextLines, type TextLine } from "./svg/TextLines.tsx";

const ID = "pipeline-map";
const WIDTH = 340;
const MARKER = arrowheadId(ID);

const FRAME_RADIUS = 14;
const FRAME_TITLE_X = 28;
const FRAME_TITLE_DROP = 22;
const FRAME_SUBTITLE_DROP = 18;
const RETURN_LABEL_X = 305;
const RETURN_LABEL_BASELINE_SHIFT = 4;
const SIDE_NOTE_X = 118;
const LINK_LABEL_GAP = 6;
const TOOLS_LINK_INSET = 30;
const TOOLS_LABEL_RISE = 9;

function centreX(box: BoxGeometry): number {
  return box.x + box.width / 2;
}

function bottom(box: BoxGeometry): number {
  return box.y + box.height;
}

function middle(box: BoxGeometry): number {
  return box.y + box.height / 2;
}

function link(from: BoxGeometry, to: BoxGeometry): string {
  return bowedPath({ x: centreX(from), y: bottom(from) }, { x: centreX(to), y: to.y });
}

function straightDown(x: number, from: number, to: number): string {
  return bowedPath({ x, y: from }, { x, y: to });
}

function LinkLabel({ at, lines }: { at: Point; lines: readonly TextLine[] }) {
  return <TextLines x={at.x} y={at.y} lines={lines} variant="note" hasHalo />;
}

function ServerFrame() {
  return (
    <g className="diagram-step" data-step={4}>
      <rect {...FRAME} rx={FRAME_RADIUS} className="diagram__frame" />
      <TextLines
        x={FRAME_TITLE_X}
        y={FRAME.y + FRAME_TITLE_DROP}
        lines={["Voice server"]}
        variant="label"
      />
      <TextLines
        x={FRAME_TITLE_X}
        y={FRAME.y + FRAME_TITLE_DROP + FRAME_SUBTITLE_DROP}
        lines={["FastAPI + Pipecat 1.12"]}
        variant="small"
      />
    </g>
  );
}

function CallerLinks() {
  const labelY = (bottom(BROWSER) + FRAME.y) / 2;
  return (
    <>
      <Arrow d={straightDown(centreX(WORKER), bottom(BROWSER), WORKER.y)} markerId={MARKER} />
      <Arrow d={straightDown(centreX(WORKER), bottom(WORKER), FRAME.y)} markerId={MARKER} />
      <Arrow d={straightDown(BROWSER_AUDIO_X, bottom(BROWSER), FRAME.y)} markerId={MARKER} />
      <Arrow d={straightDown(centreX(PHONE), bottom(PHONE), FRAME.y)} markerId={MARKER} />
      <g className="diagram-step" data-step={3}>
        <LinkLabel at={{ x: BROWSER_AUDIO_X + LINK_LABEL_GAP, y: labelY }} lines={["audio"]} />
        <LinkLabel
          at={{ x: centreX(PHONE) + LINK_LABEL_GAP, y: labelY }}
          lines={["audio +", "keypad"]}
        />
      </g>
    </>
  );
}

function AnswerLinks() {
  const fastSpeechX = FAST_PATH.x + SPEECH_INSET;
  const talkerSpeechX = TALKER.x + TALKER.width - SPEECH_INSET;
  return (
    <>
      <Arrow d={straightDown(fastSpeechX, bottom(FAST_PATH), KANA.y)} markerId={MARKER} />
      <Arrow d={straightDown(talkerSpeechX, bottom(TALKER), KANA.y)} markerId={MARKER} />
      <Arrow d={link(KANA, VOICE)} markerId={MARKER} />
    </>
  );
}

function ToolsLinks() {
  const fromFastPath = {
    x: FAST_PATH.x + FAST_PATH.width - TOOLS_LINK_INSET,
    y: bottom(FAST_PATH),
  };
  const fromTalker = { x: TALKER.x + TOOLS_LINK_INSET, y: bottom(TALKER) };
  const intoLeft = { x: DOMAIN.x + TOOLS_LINK_INSET, y: DOMAIN.y };
  const intoRight = { x: DOMAIN.x + DOMAIN.width - TOOLS_LINK_INSET, y: DOMAIN.y };
  return (
    <>
      <Arrow d={bowedPath(fromFastPath, intoLeft)} markerId={MARKER} isDashed />
      <Arrow d={bowedPath(fromTalker, intoRight)} markerId={MARKER} isDashed />
      <g className="diagram-step" data-step={9}>
        <TextLines
          x={centreX(DOMAIN)}
          y={DOMAIN.y - TOOLS_LABEL_RISE}
          lines={["via tools"]}
          variant="note"
          anchor="middle"
          hasHalo
        />
      </g>
    </>
  );
}

function ReplyLinks() {
  return (
    <>
      <Arrow d={link(HEARING, TURNS)} markerId={MARKER} />
      <Arrow d={link(TURNS, FAST_PATH)} markerId={MARKER} />
      <Arrow d={link(TURNS, TALKER)} markerId={MARKER} />
      <AnswerLinks />
      <ToolsLinks />
    </>
  );
}

function ReturnToCaller() {
  const labelY = (FRAME.y + middle(VOICE)) / 2;
  return (
    <>
      <Arrow
        d={elbowPath([
          { x: VOICE.x + VOICE.width, y: middle(VOICE) },
          { x: RETURN_X, y: middle(VOICE) },
          { x: RETURN_X, y: middle(PHONE) },
          { x: PHONE.x + PHONE.width, y: middle(PHONE) },
        ])}
        markerId={MARKER}
      />
      <g transform={`rotate(-90 ${String(RETURN_LABEL_X)} ${String(labelY)})`}>
        <TextLines
          x={RETURN_LABEL_X}
          y={labelY + RETURN_LABEL_BASELINE_SHIFT}
          lines={["his voice, back to you"]}
          variant="small"
          anchor="middle"
          hasHalo
        />
      </g>
    </>
  );
}

function SideLaneLinks() {
  const last = SIDE_LANE[SIDE_LANE.length - 1] ?? TURNS;
  return (
    <>
      <Arrow
        d={elbowPath([
          { x: TURNS.x, y: middle(TURNS) },
          { x: SIDE_RAIL_X, y: middle(TURNS) },
          { x: SIDE_RAIL_X, y: middle(last) },
          { x: last.x, y: middle(last) },
        ])}
        markerId={MARKER}
        isDashed
        hasHead={false}
      />
      {SIDE_LANE.slice(0, -1).map((box) => (
        <Arrow
          key={box.step}
          d={elbowPath([
            { x: SIDE_RAIL_X, y: middle(box) },
            { x: box.x, y: middle(box) },
          ])}
          markerId={MARKER}
          isDashed
          hasHead={false}
        />
      ))}
      <g className="diagram-step" data-step={12}>
        <TextLines x={INNER.x} y={SIDE_LABEL_Y} lines={["Side lane"]} variant="label" />
        <TextLines
          x={SIDE_NOTE_X}
          y={SIDE_LABEL_Y}
          lines={["never blocks the reply"]}
          variant="note"
        />
      </g>
    </>
  );
}

function OutputLinks() {
  return (
    <>
      <Arrow d={straightDown(centreX(EVENTS), bottom(FRAME), EVENTS.y)} markerId={MARKER} />
      <Arrow d={straightDown(centreX(AUDIT), bottom(FRAME), AUDIT.y)} markerId={MARKER} />
    </>
  );
}

const NODES: readonly LabelledBoxProps[] = [
  BROWSER,
  PHONE,
  WORKER,
  HEARING,
  TURNS,
  FAST_PATH,
  TALKER,
  DOMAIN,
  KANA,
  VOICE,
  ...SIDE_LANE,
  EVENTS,
  AUDIT,
];

/** One call through the system: callers, the voice server's pipeline, its side lane and outputs. */
export function PipelineMap() {
  return (
    <DiagramFigure
      id={ID}
      modifier="pipeline"
      width={WIDTH}
      height={HEIGHT}
      title="One call, end to end"
      description="An architecture map. A caller reaches Kenji from a browser over WebRTC, with a TURN relay if needed (the page, signalling and live events go through a Cloudflare Worker), or from a phone through Twilio Media Streams, which carries the audio and keypad. Inside the voice server, built on FastAPI and Pipecat 1.12, Silero VAD and Soniox speech recognition hear the Japanese. Turn handling combines Soniox's endpoint, Smart Turn v3, a particle rule and the Hold button. Then the fast path answers predictable turns from rules, or the talker, Muse Spark following Pipecat Flows steps, answers, checking the domain rules for identity, terms, calling hours and stop-contact through tools; those rules are pure and fully tested. The reply passes a kana normaliser and Cartesia Sonic speech synthesis, and his voice goes back to the caller. Beside the reply, never blocking it, a strategist on Muse Spark writes JSON advice for the next turn, SenseVoice hears how the caller sounds, and a translator writes English subtitles. The server publishes events over a WebSocket to the caller's own X-ray and writes a hash-chained audit log."
      heading={["One call, end to end"]}
      headingWidth={206}
      caption="Everything on the X-ray is one of 14 event types this pipeline publishes while you talk."
    >
      <ServerFrame />
      {NODES.map((node) => (
        <LabelledBox key={node.step} {...node} />
      ))}
      <CallerLinks />
      <ReplyLinks />
      <ReturnToCaller />
      <SideLaneLinks />
      <OutputLinks />
    </DiagramFigure>
  );
}
