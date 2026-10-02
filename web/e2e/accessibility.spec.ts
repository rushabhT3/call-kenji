import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import {
  DEMO_URL,
  blockBackend,
  openAfterCall,
  openMidCall,
  routeViewerFeed,
  sendViewerReady,
  serveMeasuredRecording,
} from "./support.ts";

const WCAG_AA_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];

async function expectNoAxeViolations(page: Page): Promise<void> {
  const results = await new AxeBuilder({ page }).withTags(WCAG_AA_TAGS).analyze();
  const violations = results.violations.map(
    (violation) =>
      `${violation.id}: ${violation.nodes.map((node) => node.target.join(" ")).join(", ")}`,
  );
  expect(violations).toEqual([]);
}

async function expectTabularFigures(page: Page, selectors: readonly string[]): Promise<void> {
  for (const selector of selectors) {
    const styles = await page
      .locator(selector)
      .evaluateAll((elements) =>
        elements.map((element) => getComputedStyle(element).fontVariantNumeric),
      );
    expect(styles.length, `${selector} is on the page`).toBeGreaterThan(0);
    expect(
      styles.filter((style) => !style.includes("tabular-nums")),
      `${selector} uses tabular figures`,
    ).toEqual([]);
  }
}

test.describe("WCAG 2.1 AA scan", () => {
  // Lines and the hero fade in from opacity 0, and axe would measure the contrast of a
  // half-faded frame. Reduced motion renders the same final colours with no transition.
  test.use({ reducedMotion: "reduce" });

  test("landing page", async ({ page }) => {
    const feed = await routeViewerFeed(page);
    await page.goto("/");
    sendViewerReady(await feed.connected, "4821");
    await expect(page.getByRole("group", { name: /Your code/ })).toBeVisible();

    await expectNoAxeViolations(page);
  });

  test("live view during a call", async ({ page }) => {
    await blockBackend(page);
    await serveMeasuredRecording(page);
    await openMidCall(page);

    await expectNoAxeViolations(page);
  });

  test("after the call", async ({ page }) => {
    await blockBackend(page);
    await serveMeasuredRecording(page);
    await openAfterCall(page);
    await expect(page.locator("#latency .metric__value")).toBeVisible();

    await expectNoAxeViolations(page);
  });
});

test.describe("accessibility rules", () => {
  test("keyboard focus is always visible", async ({ page }) => {
    await blockBackend(page);
    await page.goto("/");

    await page.keyboard.press("Tab");

    const outline = await page.evaluate(() => {
      const focused = document.activeElement;
      return focused ? getComputedStyle(focused).outlineStyle : "none";
    });
    expect(outline).toBe("solid");
  });

  test("reduced motion turns animation off", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await blockBackend(page);
    await page.goto(DEMO_URL);
    await expect(page.getByRole("log").getByRole("listitem").first()).toBeVisible();

    const durations = await page.evaluate(() =>
      [...document.querySelectorAll(".line, .hero > *, .live-status__dot")].map(
        (element) => getComputedStyle(element).animationDuration,
      ),
    );
    expect(durations.every((duration) => parseFloat(duration) <= 0.0001)).toBe(true);
  });

  test("numbers before a call use tabular figures", async ({ page }) => {
    const feed = await routeViewerFeed(page);
    await page.goto("/");
    sendViewerReady(await feed.connected, "4821");
    await expect(page.getByRole("group", { name: /Your code/ })).toBeVisible();

    await expectTabularFigures(page, [".role__value", ".link-code__cell"]);
  });

  test("numbers during and after a call use tabular figures", async ({ page }) => {
    await blockBackend(page);
    await serveMeasuredRecording(page);
    await openAfterCall(page);
    await expect(page.locator("#latency .metric__value")).toBeVisible();

    await expectTabularFigures(page, [
      ".live-status time",
      ".line__meta time",
      "#latency .metric__value",
      "#latency .stage__value",
      ".latency__percentiles",
      ".budget__marker-label",
      "#turn .measures dd",
      ".chips__link",
      ".pill",
      "#strategist .offers li",
      ".outcome__metric",
      ".outcome__fact",
      "#sms .numeric",
      "#handoff time",
    ]);
  });

  test("Japanese text is marked and spaced for reading", async ({ page }) => {
    await blockBackend(page);
    await page.goto(DEMO_URL);
    const line = page.getByRole("log").locator(".line__ja").first();
    await expect(line).toBeVisible();

    const style = await line.evaluate((element) => {
      const computed = getComputedStyle(element);
      return {
        lang: element.getAttribute("lang"),
        ratio: parseFloat(computed.lineHeight) / parseFloat(computed.fontSize),
      };
    });
    expect(style.lang).toBe("ja");
    expect(style.ratio).toBeGreaterThanOrEqual(1.7);
  });
});
