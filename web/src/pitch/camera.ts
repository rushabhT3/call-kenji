export interface Size {
  width: number;
  height: number;
}

export interface Point {
  x: number;
  y: number;
}

/** A box laid out inside a stop, in the stop's own unscaled pixels, from its top left corner. */
export interface LocalRect extends Point, Size {}

/** Where a stop sits in the world: its centre, its scale and its tilt in degrees. */
export interface Placement extends Point {
  scale: number;
  rotate: number;
}

/** What the camera frames: a centre, a size and a tilt, all in world units. */
export interface Frame extends Size {
  cx: number;
  cy: number;
  rotate: number;
}

/** The camera's transform: the world moves by x and y, then turns and scales about the centre. */
export interface CameraState extends Point {
  scale: number;
  rotation: number;
}

/** Share of the viewport left empty around a framed box, so it never touches the edges. */
export const FRAME_PADDING = 0.08;
/** A tiny box is never blown up past this, so a short stop does not fill the screen with type. */
export const MAX_SCALE = 1.35;

const DEGREES_TO_RADIANS = Math.PI / 180;

function rotatePoint({ x, y }: Point, degrees: number): Point {
  const angle = degrees * DEGREES_TO_RADIANS;
  return {
    x: x * Math.cos(angle) - y * Math.sin(angle),
    y: x * Math.sin(angle) + y * Math.cos(angle),
  };
}

/** The world frame of a stop, or of one box inside it when the camera zooms in further. */
export function frameOf(placement: Placement, box: Size, focus?: LocalRect): Frame {
  const local = focus ?? { x: 0, y: 0, ...box };
  const offset = rotatePoint(
    {
      x: (local.x + local.width / 2 - box.width / 2) * placement.scale,
      y: (local.y + local.height / 2 - box.height / 2) * placement.scale,
    },
    placement.rotate,
  );
  return {
    cx: placement.x + offset.x,
    cy: placement.y + offset.y,
    width: local.width * placement.scale,
    height: local.height * placement.scale,
    rotate: placement.rotate,
  };
}

function corners(frame: Frame): Point[] {
  const halfWidth = frame.width / 2;
  const halfHeight = frame.height / 2;
  return [
    { x: -halfWidth, y: -halfHeight },
    { x: halfWidth, y: -halfHeight },
    { x: halfWidth, y: halfHeight },
    { x: -halfWidth, y: halfHeight },
  ].map((corner) => {
    const turned = rotatePoint(corner, frame.rotate);
    return { x: frame.cx + turned.x, y: frame.cy + turned.y };
  });
}

/** The upright box that holds every frame given, tilted or not. */
export function boundsOf(frames: readonly Frame[]): Frame {
  const points = frames.flatMap(corners);
  const xs = points.map((point) => point.x);
  const ys = points.map((point) => point.y);
  const left = Math.min(...xs);
  const top = Math.min(...ys);
  const width = Math.max(...xs) - left;
  const height = Math.max(...ys) - top;
  return { cx: left + width / 2, cy: top + height / 2, width, height, rotate: 0 };
}

/** The scale at which a frame fills the viewport, less the padding, and never past the cap. */
export function fitScale(viewport: Size, frame: Size, padding = FRAME_PADDING): number {
  const room = 1 - padding * 2;
  return Math.min(
    (viewport.width * room) / frame.width,
    (viewport.height * room) / frame.height,
    MAX_SCALE,
  );
}

/** The camera transform that centres a frame, turns it upright and fits it to the viewport. */
export function cameraFor(viewport: Size, frame: Frame): CameraState {
  return { x: -frame.cx, y: -frame.cy, scale: fitScale(viewport, frame), rotation: -frame.rotate };
}

/**
 * How far to pull back while flying between two frames: far enough to see both, the way Prezi
 * zooms out before it travels. Neighbouring boxes need no pull-back at all.
 */
export function travelScale(viewport: Size, from: Frame, to: Frame): number {
  return Math.min(
    fitScale(viewport, from),
    fitScale(viewport, to),
    fitScale(viewport, boundsOf([from, to])),
  );
}

/** Share of a page shown again at the top of the next one, so the reader keeps their place. */
export const PAGE_OVERLAP = 0.12;
/** Page a frame only when fitting all of it would shrink its type below this share. */
export const PAGING_THRESHOLD = 0.75;

/**
 * A frame too tall to read whole is shown in pages: each as wide as the frame and as tall as the
 * viewport allows at that width, the camera panning down it like a scroll.
 */
export function pagesOf(viewport: Size, frame: Frame): Frame[] {
  const room = 1 - FRAME_PADDING * 2;
  const widthScale = Math.min((viewport.width * room) / frame.width, MAX_SCALE);
  // Natural size is the yardstick: a close-up that reads well whole is not paged for being zoomable.
  if (fitScale(viewport, frame) >= Math.min(widthScale, 1) * PAGING_THRESHOLD) {
    return [frame];
  }
  const visible = (viewport.height * room) / widthScale;
  const stride = visible * (1 - PAGE_OVERLAP);
  const count = Math.ceil((frame.height - visible) / stride) + 1;
  return Array.from({ length: count }, (_, index) => {
    const top = Math.min(index * stride, frame.height - visible);
    const shift = rotatePoint({ x: 0, y: top + visible / 2 - frame.height / 2 }, frame.rotate);
    return { ...frame, cx: frame.cx + shift.x, cy: frame.cy + shift.y, height: visible };
  });
}

function rounded(value: number): string {
  return String(Math.round(value));
}

/** A hand-drawn curve from one point to another, bowed to one side by a share of its length. */
export function doodlePath(from: Point, to: Point, bow: number): string {
  const middle = { x: (from.x + to.x) / 2, y: (from.y + to.y) / 2 };
  const control = { x: middle.x - (to.y - from.y) * bow, y: middle.y + (to.x - from.x) * bow };
  const start = `M ${rounded(from.x)} ${rounded(from.y)}`;
  return `${start} Q ${rounded(control.x)} ${rounded(control.y)} ${rounded(to.x)} ${rounded(to.y)}`;
}
