import { describe, expect, it } from "vitest";
import { burstPoints, seededRandom, toSvgPoints } from "./burstShape.ts";

const SHAPE = { spikes: 12, innerRatio: 0.7, wobble: 0.08, seed: 7 };

const distance = ({ x, y }: { x: number; y: number }) => Math.hypot(x, y);

describe("burstPoints", () => {
  it("draws a spike and a valley for every spike asked for", () => {
    expect(burstPoints(SHAPE)).toHaveLength(24);
  });

  it("keeps every spike further out than every valley", () => {
    const points = burstPoints(SHAPE);
    const spikes = points.filter((_, index) => index % 2 === 0).map(distance);
    const valleys = points.filter((_, index) => index % 2 === 1).map(distance);

    expect(Math.min(...spikes)).toBeGreaterThan(Math.max(...valleys));
  });

  it("draws the same outline for the same seed", () => {
    expect(burstPoints(SHAPE)).toEqual(burstPoints(SHAPE));
    expect(burstPoints({ ...SHAPE, seed: 8 })).not.toEqual(burstPoints(SHAPE));
  });
});

describe("seededRandom", () => {
  it("stays between 0 and 1", () => {
    const random = seededRandom(42);
    const draws = Array.from({ length: 200 }, random);

    expect(draws.every((draw) => draw >= 0 && draw < 1)).toBe(true);
  });
});

describe("toSvgPoints", () => {
  it("maps the unit square onto the box", () => {
    expect(
      toSvgPoints(
        [
          { x: -1, y: -1 },
          { x: 1, y: 1 },
        ],
        300,
        200,
      ),
    ).toBe("0,0 300,200");
  });
});
