const MILLISECONDS_PER_SECOND = 1000;

export function formatMilliseconds(milliseconds: number): string {
  if (milliseconds < MILLISECONDS_PER_SECOND) {
    return `${String(Math.round(milliseconds))} ms`;
  }
  return `${(milliseconds / MILLISECONDS_PER_SECOND).toFixed(2)} s`;
}
