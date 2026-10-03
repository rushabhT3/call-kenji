import { describe, expect, it } from "vitest";
import { pageForPath } from "./pages.ts";

describe("pageForPath", () => {
  it("finds each named page, with or without a trailing slash", () => {
    expect(pageForPath("/features")).toBe("showcase");
    expect(pageForPath("/pitch/")).toBe("pitch");
    expect(pageForPath("/trailer")).toBe("trailer");
  });

  it("shows the call page for every other address", () => {
    expect(pageForPath("/")).toBe("call");
    expect(pageForPath("/features/extra")).toBe("call");
  });
});
