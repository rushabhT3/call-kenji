import { describe, expect, it } from "vitest";
import {
  boundsOf,
  cameraFor,
  doodlePath,
  fitScale,
  frameOf,
  MAX_SCALE,
  pagesOf,
  travelScale,
  type Frame,
} from "./camera.ts";

const VIEWPORT = { width: 1000, height: 800 };
const BOX = { width: 400, height: 200 };

describe("frameOf", () => {
  it("frames the whole stop at its placement, scaled", () => {
    const frame = frameOf({ x: 500, y: 300, scale: 2, rotate: 0 }, BOX);

    expect(frame).toEqual({ cx: 500, cy: 300, width: 800, height: 400, rotate: 0 });
  });

  it("finds a box inside a turned stop", () => {
    const focus = { x: 300, y: 0, width: 100, height: 200 };

    const frame = frameOf({ x: 0, y: 0, scale: 1, rotate: 90 }, BOX, focus);

    expect(frame.cx).toBeCloseTo(0);
    expect(frame.cy).toBeCloseTo(150);
    expect(frame).toMatchObject({ width: 100, height: 200, rotate: 90 });
  });
});

describe("boundsOf", () => {
  it("holds every corner of a turned frame", () => {
    const turned: Frame = { cx: 0, cy: 0, width: 200, height: 100, rotate: 90 };

    const bounds = boundsOf([turned]);

    expect(bounds.width).toBeCloseTo(100);
    expect(bounds.height).toBeCloseTo(200);
  });

  it("spans two frames far apart", () => {
    const left: Frame = { cx: 0, cy: 0, width: 100, height: 100, rotate: 0 };
    const right: Frame = { cx: 1000, cy: 0, width: 100, height: 100, rotate: 0 };

    expect(boundsOf([left, right])).toMatchObject({ cx: 500, cy: 0, width: 1100, height: 100 });
  });
});

describe("fitScale", () => {
  it("fits the tighter side, leaving the padding free", () => {
    expect(fitScale(VIEWPORT, { width: 840, height: 100 })).toBeCloseTo(1);
  });

  it("never blows a small box up past the cap", () => {
    expect(fitScale(VIEWPORT, { width: 10, height: 10 })).toBe(MAX_SCALE);
  });
});

describe("cameraFor", () => {
  it("moves the frame to the centre and turns it upright", () => {
    const camera = cameraFor(VIEWPORT, { cx: 300, cy: 200, width: 840, height: 100, rotate: 4 });

    expect(camera).toMatchObject({ x: -300, y: -200, rotation: -4 });
    expect(camera.scale).toBeCloseTo(1);
  });
});

describe("travelScale", () => {
  it("pulls back to show both frames when they are far apart", () => {
    const from: Frame = { cx: 0, cy: 0, width: 400, height: 200, rotate: 0 };
    const to: Frame = { cx: 5000, cy: 0, width: 400, height: 200, rotate: 0 };

    expect(travelScale(VIEWPORT, from, to)).toBeLessThan(fitScale(VIEWPORT, to) / 5);
  });

  it("does not pull back between overlapping frames", () => {
    const from: Frame = { cx: 0, cy: 0, width: 400, height: 200, rotate: 0 };
    const to: Frame = { cx: 0, cy: 0, width: 200, height: 100, rotate: 0 };

    expect(travelScale(VIEWPORT, from, to)).toBe(fitScale(VIEWPORT, from));
  });
});

describe("pagesOf", () => {
  it("keeps a frame that fits as one page", () => {
    const frame: Frame = { cx: 0, cy: 0, width: 800, height: 400, rotate: 0 };

    expect(pagesOf(VIEWPORT, frame)).toEqual([frame]);
  });

  it("pages a tall frame from top to bottom, ending flush with its bottom", () => {
    const frame: Frame = { cx: 0, cy: 0, width: 840, height: 2000, rotate: 0 };

    const pages = pagesOf(VIEWPORT, frame);
    const last = pages.at(-1);

    expect(pages.length).toBeGreaterThan(1);
    expect(pages[0]?.cy).toBeCloseTo(-1000 + (pages[0]?.height ?? 0) / 2);
    expect(last?.cy).toBeCloseTo(1000 - (last?.height ?? 0) / 2);
    expect(pages.every((page) => fitScale(VIEWPORT, page) >= 0.99)).toBe(true);
  });

  it("pages along a turned frame's own length", () => {
    const frame: Frame = { cx: 0, cy: 0, width: 840, height: 2000, rotate: 90 };

    const [first] = pagesOf(VIEWPORT, frame);

    expect(first?.cy).toBeCloseTo(0);
    expect(first?.cx).toBeGreaterThan(0);
  });
});

describe("doodlePath", () => {
  it("draws a curve that starts and ends on the two points", () => {
    expect(doodlePath({ x: 0, y: 0 }, { x: 100, y: 0 }, 0.2)).toBe("M 0 0 Q 50 20 100 0");
  });
});
