import { boundsOf, frameOf, pagesOf, type Frame, type LocalRect, type Size } from "./camera.ts";
import { CENTRE_BURST, STEPS, STOPS, type StepData } from "./stops.ts";

function required(scope: ParentNode, selector: string): HTMLElement {
  const element = scope.querySelector<HTMLElement>(selector);
  if (!element) {
    throw new Error(`The pitch is missing ${selector}`);
  }
  return element;
}

/** Where a box sits inside a stop, from layout offsets, which the world's transforms leave alone. */
function localRect(element: HTMLElement, stop: HTMLElement): LocalRect {
  let x = 0;
  let y = 0;
  let current: HTMLElement | null = element;
  while (current && current !== stop) {
    x += current.offsetLeft;
    y += current.offsetTop;
    current = current.offsetParent as HTMLElement | null;
  }
  return { x, y, width: element.offsetWidth, height: element.offsetHeight };
}

function boxOf(element: HTMLElement): Size {
  return { width: element.offsetWidth, height: element.offsetHeight };
}

function stepFrame(world: HTMLElement, step: StepData): Frame {
  const stop = required(world, `[data-stop="${step.stop}"]`);
  const placement = STOPS.find((candidate) => candidate.id === step.stop)?.placement;
  if (!placement) {
    throw new Error(`No placement for the ${step.stop} stop`);
  }
  const focus = step.focus
    ? localRect(required(stop, `[data-focus="${step.focus}"]`), stop)
    : undefined;
  return frameOf(placement, boxOf(stop), focus);
}

/**
 * Every step's pages, measured from the laid-out world for this viewport. Step 0 is the whole
 * universe, always one page; a tall stop gets as many pages as it needs to stay readable.
 */
export function measureFrames(world: HTMLElement, viewport: Size): Frame[][] {
  const stops = STEPS.map((step) => stepFrame(world, step));
  const burst = frameOf(CENTRE_BURST, boxOf(required(world, "[data-burst]")));
  return [[boundsOf([...stops, burst])], ...stops.map((frame) => pagesOf(viewport, frame))];
}
