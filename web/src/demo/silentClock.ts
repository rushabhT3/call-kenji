import { ClockListeners, type ReplayClock } from "./clock.ts";
import { clampPosition } from "./playhead.ts";

/** The page's clock and its animation frames; tests drive a fake one. */
export interface FrameScheduler {
  now: () => number;
  request: (onFrame: () => void) => number;
  cancel: (frame: number) => void;
}

const BROWSER_FRAMES: FrameScheduler = {
  now: () => performance.now(),
  request: (onFrame) => window.requestAnimationFrame(onFrame),
  cancel: (frame) => {
    window.cancelAnimationFrame(frame);
  },
};

interface SilentClockOptions {
  durationMs: number;
  /** How many milliseconds of the call pass in one millisecond on the page. */
  rate: number;
  frames?: FrameScheduler;
}

interface Run {
  fromMs: number;
  startedAt: number;
}

/** Runs a replay with no sound, on the page's own clock, at any speed. */
export class SilentClock implements ReplayClock {
  readonly hasSound = false;
  readonly durationMs: number;
  private readonly rate: number;
  private readonly frames: FrameScheduler;
  private readonly listeners = new ClockListeners();
  private position = 0;
  private run: Run | null = null;
  private frame: number | null = null;

  constructor({ durationMs, rate, frames = BROWSER_FRAMES }: SilentClockOptions) {
    if (!Number.isFinite(rate) || rate <= 0) {
      throw new Error(`replay speed must be positive, got ${String(rate)}`);
    }
    this.durationMs = Math.max(0, durationMs);
    this.rate = rate;
    this.frames = frames;
  }

  positionMs(): number {
    return this.position;
  }

  isPlaying(): boolean {
    return this.run !== null;
  }

  play(): Promise<void> {
    if (this.run === null) {
      if (this.position >= this.durationMs) {
        this.position = 0;
      }
      this.startRun();
      this.notify();
    }
    return Promise.resolve();
  }

  pause(): void {
    if (this.run !== null) {
      this.position = this.runPosition(this.run);
      this.stopRun();
      this.notify();
    }
  }

  seek(positionMs: number): void {
    this.position = clampPosition(positionMs, this.durationMs);
    if (this.run !== null) {
      this.run = { fromMs: this.position, startedAt: this.frames.now() };
    }
    this.notify();
  }

  subscribe(onChange: () => void): () => void {
    return this.listeners.add(onChange);
  }

  private readonly tick = () => {
    this.frame = null;
    if (this.run === null) {
      return;
    }
    this.position = this.runPosition(this.run);
    if (this.position >= this.durationMs) {
      this.stopRun();
    } else {
      this.frame = this.frames.request(this.tick);
    }
    this.notify();
  };

  private runPosition(run: Run): number {
    const elapsed = (this.frames.now() - run.startedAt) * this.rate;
    return clampPosition(run.fromMs + elapsed, this.durationMs);
  }

  private startRun(): void {
    this.run = { fromMs: this.position, startedAt: this.frames.now() };
    this.frame = this.frames.request(this.tick);
  }

  private stopRun(): void {
    this.run = null;
    if (this.frame !== null) {
      this.frames.cancel(this.frame);
      this.frame = null;
    }
  }

  private notify(): void {
    this.listeners.notify();
  }
}
