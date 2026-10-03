import { describe, expect, it } from "vitest";
import { firstStepOf, LAST_STEP, stepFromHash, stepLabel, STEPS, STOPS } from "./stops.ts";

describe("stepFromHash", () => {
  it("opens at the step the address names", () => {
    expect(stepFromHash("#3")).toBe(3);
  });

  it("opens at the overview for an empty, unknown or out-of-range address", () => {
    expect(stepFromHash("")).toBe(0);
    expect(stepFromHash("#x-ray")).toBe(0);
    expect(stepFromHash(`#${String(LAST_STEP + 1)}`)).toBe(0);
  });
});

describe("firstStepOf", () => {
  it("lands on the whole X-ray before its close-ups", () => {
    expect(STEPS[firstStepOf("xray") - 1]).toEqual({ stop: "xray", label: "The live X-ray" });
  });
});

describe("the story", () => {
  it("visits every stop", () => {
    const visited = new Set(STEPS.map((step) => step.stop));

    expect(STOPS.every((stop) => visited.has(stop.id))).toBe(true);
  });

  it("names the overview and every step", () => {
    expect(stepLabel(0)).toBe("The whole universe");
    expect(stepLabel(LAST_STEP)).toBe("Your turn");
  });
});
