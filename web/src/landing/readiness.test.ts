import { describe, expect, it } from "vitest";
import { serverReadiness } from "./readiness.ts";

describe("serverReadiness", () => {
  it("is ready once the page has its viewer link", () => {
    expect(serverReadiness("viewer-1", "open")).toBe("ready");
  });

  it("is waking while the page waits for the server to answer", () => {
    expect(serverReadiness(null, "connecting")).toBe("waking");
    expect(serverReadiness(null, "open")).toBe("waking");
  });

  it("is unreachable when the feed is lost before the server answered", () => {
    expect(serverReadiness(null, "lost")).toBe("unreachable");
  });
});
