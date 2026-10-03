/**
 * What a replay runs on: where it is in the call, and whether it is moving. Reads return the
 * value as of the last change it announced, so a render always sees one consistent moment.
 */
export interface ReplayClock {
  readonly hasSound: boolean;
  readonly durationMs: number;
  positionMs(): number;
  isPlaying(): boolean;
  play(): Promise<void>;
  pause(): void;
  seek(positionMs: number): void;
  /** Calls back on every change of position or of playing; returns the way to stop. */
  subscribe(onChange: () => void): () => void;
}

/** The listeners of one clock, told about each change in the order they subscribed. */
export class ClockListeners {
  private readonly listeners = new Set<() => void>();

  add(onChange: () => void): () => void {
    this.listeners.add(onChange);
    return () => {
      this.listeners.delete(onChange);
    };
  }

  notify(): void {
    this.listeners.forEach((onChange) => {
      onChange();
    });
  }
}
