import { describe, expect, it } from "vitest";
import {
  formatClock,
  formatCount,
  formatMilliseconds,
  formatScore,
  formatTime,
  isoDuration,
} from "./format.ts";

describe("formatMilliseconds", () => {
  it("shows sub-second values as whole milliseconds", () => {
    expect(formatMilliseconds(412.6)).toBe("413 ms");
  });

  it("shows longer values as seconds with two decimals", () => {
    expect(formatMilliseconds(1520)).toBe("1.52 s");
  });
});

describe("numbers and clocks", () => {
  it("groups thousands", () => {
    expect(formatCount(35000)).toBe("35,000");
  });

  it("shows call-relative time as mm:ss", () => {
    expect(formatClock(134_400)).toBe("02:14");
    expect(formatClock(-5)).toBe("00:00");
  });

  it("writes a machine-readable duration", () => {
    expect(isoDuration(134_400)).toBe("PT134S");
  });

  it("shows scores with two decimals", () => {
    expect(formatScore(0.5)).toBe("0.50");
  });

  it("shows wall-clock times in Japan time", () => {
    expect(formatTime("2026-10-02T06:05:00Z")).toBe("15:05");
  });
});
