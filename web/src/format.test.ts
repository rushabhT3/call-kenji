import { describe, expect, it } from "vitest";
import { formatMilliseconds } from "./format.ts";

describe("formatMilliseconds", () => {
  it("shows sub-second values as whole milliseconds", () => {
    expect(formatMilliseconds(412.6)).toBe("413 ms");
  });

  it("shows longer values as seconds with two decimals", () => {
    expect(formatMilliseconds(1520)).toBe("1.52 s");
  });
});
