import { describe, expect, it } from "vitest";
import { SilentClock, type FrameScheduler } from "./silentClock.ts";

/** A page clock the test moves by hand, running whichever frame is waiting. */
function fakeFrames() {
  let now = 0;
  let waiting: (() => void) | null = null;
  const frames: FrameScheduler = {
    now: () => now,
    request: (onFrame) => {
      waiting = onFrame;
      return 1;
    },
    cancel: () => {
      waiting = null;
    },
  };
  const advance = (milliseconds: number) => {
    now += milliseconds;
    const frame = waiting;
    waiting = null;
    frame?.();
  };
  return { frames, advance };
}

describe("SilentClock", () => {
  it("advances at its speed while playing", async () => {
    const { frames, advance } = fakeFrames();
    const clock = new SilentClock({ durationMs: 10_000, rate: 4, frames });

    await clock.play();
    advance(500);

    expect(clock.positionMs()).toBe(2000);
    expect(clock.isPlaying()).toBe(true);
  });

  it("stands still while paused", async () => {
    const { frames, advance } = fakeFrames();
    const clock = new SilentClock({ durationMs: 10_000, rate: 1, frames });
    await clock.play();
    advance(1000);

    clock.pause();
    advance(5000);

    expect(clock.positionMs()).toBe(1000);
    expect(clock.isPlaying()).toBe(false);
  });

  it("carries on from wherever it is moved to", async () => {
    const { frames, advance } = fakeFrames();
    const clock = new SilentClock({ durationMs: 10_000, rate: 1, frames });
    await clock.play();

    clock.seek(7000);
    advance(1000);

    expect(clock.positionMs()).toBe(8000);
  });

  it("stops at the end of the call, and plays again from the start", async () => {
    const { frames, advance } = fakeFrames();
    const clock = new SilentClock({ durationMs: 3000, rate: 2, frames });
    await clock.play();
    advance(5000);

    expect(clock.positionMs()).toBe(3000);
    expect(clock.isPlaying()).toBe(false);

    await clock.play();
    expect(clock.positionMs()).toBe(0);
  });

  it("tells its listeners about every change until they stop listening", async () => {
    const { frames, advance } = fakeFrames();
    const clock = new SilentClock({ durationMs: 10_000, rate: 1, frames });
    let changes = 0;
    const stop = clock.subscribe(() => {
      changes += 1;
    });

    await clock.play();
    advance(100);
    stop();
    advance(100);

    expect(changes).toBe(2);
  });

  it("refuses a speed that cannot play", () => {
    expect(() => new SilentClock({ durationMs: 1000, rate: 0 })).toThrow("positive");
  });
});
