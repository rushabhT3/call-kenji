import { describe, expect, it } from "vitest";
import { clampPosition, keyedPosition, positionAtPointer, settledPosition } from "./playhead.ts";
import type { Timeline } from "./timeline.ts";

const timeline: Timeline = {
  events: [
    { atMs: 0, event: { type: "flow_node", node: "greeting" } },
    { atMs: 2350, event: { type: "flow_node", node: "verify_identity" } },
  ],
  durationMs: 9000,
};

describe("settledPosition", () => {
  it("holds still between one change on screen and the next", () => {
    expect(settledPosition(timeline, 1999)).toBe(1000);
    expect(settledPosition(timeline, 2349)).toBe(2000);
  });

  it("moves on the moment an event happens", () => {
    expect(settledPosition(timeline, 2350)).toBe(2350);
    expect(settledPosition(timeline, 2999)).toBe(2350);
  });

  it("moves on when the clock shows the next second", () => {
    expect(settledPosition(timeline, 3000)).toBe(3000);
  });

  it("never settles before the start of the call", () => {
    expect(settledPosition(timeline, -40)).toBe(0);
  });
});

describe("keyedPosition", () => {
  it("steps five seconds with the arrow keys", () => {
    expect(keyedPosition("ArrowRight", 4000, 9000)).toBe(9000);
    expect(keyedPosition("ArrowLeft", 4000, 9000)).toBe(0);
    expect(keyedPosition("ArrowUp", 1000, 9000)).toBe(6000);
  });

  it("jumps to either end with Home and End", () => {
    expect(keyedPosition("Home", 4000, 9000)).toBe(0);
    expect(keyedPosition("End", 4000, 9000)).toBe(9000);
  });

  it("ignores any other key", () => {
    expect(keyedPosition("Enter", 4000, 9000)).toBeNull();
  });
});

describe("positionAtPointer", () => {
  const track = { left: 100, width: 200 };

  it("maps the pointer across the track onto the call", () => {
    expect(positionAtPointer(150, track, 8000)).toBe(2000);
  });

  it("keeps a drag past either end inside the call", () => {
    expect(positionAtPointer(40, track, 8000)).toBe(0);
    expect(positionAtPointer(400, track, 8000)).toBe(8000);
  });

  it("stays at the start on a track with no width", () => {
    expect(positionAtPointer(150, { left: 100, width: 0 }, 8000)).toBe(0);
  });
});

describe("clampPosition", () => {
  it("keeps a position within the call", () => {
    expect(clampPosition(-1, 500)).toBe(0);
    expect(clampPosition(501, 500)).toBe(500);
    expect(clampPosition(250, 500)).toBe(250);
  });
});
