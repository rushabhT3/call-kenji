import type WaveSurfer from "wavesurfer.js";
import { ClockListeners, type ReplayClock } from "./clock.ts";
import { clampPosition } from "./playhead.ts";

const MILLISECONDS_PER_SECOND = 1000;

/**
 * The recording's own sound as the replay's clock: the screen follows what is heard, so the two
 * never drift apart. Wraps a waveform that has loaded.
 */
export class WaveformClock implements ReplayClock {
  readonly hasSound = true;
  readonly durationMs: number;
  private readonly waveSurfer: WaveSurfer;
  private readonly listeners = new ClockListeners();
  private position: number;
  private playing: boolean;

  constructor(waveSurfer: WaveSurfer) {
    this.waveSurfer = waveSurfer;
    this.durationMs = waveSurfer.getDuration() * MILLISECONDS_PER_SECOND;
    this.position = waveSurfer.getCurrentTime() * MILLISECONDS_PER_SECOND;
    this.playing = waveSurfer.isPlaying();
    waveSurfer.on("timeupdate", (seconds) => {
      this.update(seconds * MILLISECONDS_PER_SECOND, this.playing);
    });
    waveSurfer.on("play", () => {
      this.update(this.position, true);
    });
    waveSurfer.on("pause", () => {
      this.update(this.position, false);
    });
    waveSurfer.on("finish", () => {
      this.update(this.durationMs, false);
    });
  }

  positionMs(): number {
    return this.position;
  }

  isPlaying(): boolean {
    return this.playing;
  }

  async play(): Promise<void> {
    await this.waveSurfer.play();
  }

  pause(): void {
    this.waveSurfer.pause();
  }

  seek(positionMs: number): void {
    const target = clampPosition(positionMs, this.durationMs);
    this.waveSurfer.setTime(target / MILLISECONDS_PER_SECOND);
  }

  subscribe(onChange: () => void): () => void {
    return this.listeners.add(onChange);
  }

  private update(positionMs: number, isPlaying: boolean): void {
    this.position = positionMs;
    this.playing = isPlaying;
    this.listeners.notify();
  }
}
