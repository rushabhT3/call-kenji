export interface Point {
  x: number;
  y: number;
}

export interface BurstShape {
  spikes: number;
  /** How far the valleys sit from the centre, as a share of the spike length. */
  innerRatio: number;
  /** How much each point strays, as a share of its radius, so the outline looks drawn by hand. */
  wobble: number;
  seed: number;
}

const FULL_TURN = Math.PI * 2;
const UINT32 = 2 ** 32;

/** Mulberry32: a tiny seeded generator, so a burst has the same outline on every render. */
export function seededRandom(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let mixed = Math.imul(state ^ (state >>> 15), 1 | state);
    mixed = (mixed + Math.imul(mixed ^ (mixed >>> 7), 61 | mixed)) ^ mixed;
    return ((mixed ^ (mixed >>> 14)) >>> 0) / UINT32;
  };
}

/** The outline of a comic starburst on the unit circle: spike, valley, spike, valley… */
export function burstPoints(shape: BurstShape): Point[] {
  const random = seededRandom(shape.seed);
  const step = FULL_TURN / (shape.spikes * 2);
  return Array.from({ length: shape.spikes * 2 }, (_, index) => {
    const base = index % 2 === 0 ? 1 : shape.innerRatio;
    const radius = base * (1 - shape.wobble * random());
    const angle = index * step + (random() - 0.5) * step * shape.wobble * 2;
    return { x: Math.cos(angle) * radius, y: Math.sin(angle) * radius };
  });
}

/** Stretches unit points over a box of the given size, centred in it. */
export function toSvgPoints(points: readonly Point[], width: number, height: number): string {
  return points
    .map(({ x, y }) => `${String(((x + 1) * width) / 2)},${String(((y + 1) * height) / 2)}`)
    .join(" ");
}
