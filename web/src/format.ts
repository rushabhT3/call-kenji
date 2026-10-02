const MILLISECONDS_PER_SECOND = 1000;
const SECONDS_PER_MINUTE = 60;
const numbers = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

export function formatMilliseconds(milliseconds: number): string {
  if (milliseconds < MILLISECONDS_PER_SECOND) {
    return `${String(Math.round(milliseconds))} ms`;
  }
  return `${(milliseconds / MILLISECONDS_PER_SECOND).toFixed(2)} s`;
}

export function formatCount(value: number): string {
  return numbers.format(value);
}

export function formatClock(milliseconds: number): string {
  const totalSeconds = Math.floor(Math.max(0, milliseconds) / MILLISECONDS_PER_SECOND);
  const minutes = Math.floor(totalSeconds / SECONDS_PER_MINUTE);
  const seconds = totalSeconds % SECONDS_PER_MINUTE;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

export function isoDuration(milliseconds: number): string {
  return `PT${String(Math.floor(Math.max(0, milliseconds) / MILLISECONDS_PER_SECOND))}S`;
}

export function formatScore(score: number): string {
  return score.toFixed(2);
}

export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Asia/Tokyo",
  });
}
