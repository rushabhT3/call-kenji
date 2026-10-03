import { describe, expect, it } from "vitest";
import { isAtEnd, nextPosition, previousPosition, startOf } from "./position.ts";
import { LAST_STEP } from "./stops.ts";

const PAGES = [1, 1, 3, 1];

describe("nextPosition", () => {
  it("pages down a tall step before moving on", () => {
    expect(nextPosition({ step: 2, page: 0 }, PAGES)).toEqual({ step: 2, page: 1 });
    expect(nextPosition({ step: 2, page: 2 }, PAGES)).toEqual({ step: 3, page: 0 });
  });

  it("stays on the last page of the last step", () => {
    const end = { step: LAST_STEP, page: 0 };

    expect(nextPosition(end, PAGES)).toBe(end);
    expect(isAtEnd(end, PAGES)).toBe(true);
  });
});

describe("previousPosition", () => {
  it("backs up into the last page of a tall step", () => {
    expect(previousPosition({ step: 3, page: 0 }, PAGES)).toEqual({ step: 2, page: 2 });
  });

  it("stays on the overview", () => {
    const overview = { step: 0, page: 0 };

    expect(previousPosition(overview, PAGES)).toBe(overview);
  });
});

describe("startOf", () => {
  it("clamps a jump to the story's ends", () => {
    expect(startOf(-4)).toEqual({ step: 0, page: 0 });
    expect(startOf(LAST_STEP + 9)).toEqual({ step: LAST_STEP, page: 0 });
  });
});
