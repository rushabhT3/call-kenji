import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Locator, type Page } from "@playwright/test";
import { WIDTHS, blockBackend } from "./support.ts";

const SHOWCASE_URL = "/features";
const WCAG_AA_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];
const SIDEWAYS_SCROLL_TIMEOUT_MS = 180_000;
const SCROLL_STEP_PX = 600;
const SCROLL_PAUSE_MS = 120;
const COUNT_UP_TIMEOUT_MS = 10_000;
const FINAL_STATS = ["0.7 s", "24/24", "100%", "14", "52"];
const XRAY_CALLOUTS = 5;
const STACK_CARDS = 12;

async function expectNoAxeViolations(page: Page): Promise<void> {
  const results = await new AxeBuilder({ page }).withTags(WCAG_AA_TAGS).analyze();
  const violations = results.violations.map(
    (violation) =>
      `${violation.id}: ${violation.nodes.map((node) => node.target.join(" ")).join(", ")}`,
  );
  expect(violations).toEqual([]);
}

/** Scroll to the bottom a screen at a time, so lazy images load and scroll animations run. */
async function scrollThrough(page: Page): Promise<void> {
  let atBottom = false;
  while (!atBottom) {
    atBottom = await page.evaluate((step) => {
      window.scrollBy(0, step);
      return window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 1;
    }, SCROLL_STEP_PX);
    await page.waitForTimeout(SCROLL_PAUSE_MS);
  }
}

async function openShowcase(page: Page): Promise<void> {
  await page.goto(SHOWCASE_URL);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
}

async function expectAllShown(cards: Locator, count: number): Promise<void> {
  await expect(cards).toHaveCount(count);
  const styles = await cards.evaluateAll((elements) =>
    elements.map((element) => {
      const style = getComputedStyle(element);
      return { opacity: style.opacity, visibility: style.visibility };
    }),
  );
  expect(styles).toEqual(
    Array.from({ length: count }, () => ({ opacity: "1", visibility: "visible" })),
  );
}

test.describe("features page", () => {
  test("the landing page's Features link opens it", async ({ page }) => {
    await blockBackend(page);
    await page.goto("/");

    await page.getByRole("link", { name: "Features", exact: true }).click();

    await expect(page).toHaveURL(/\/features$/);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(
      /^A Japanese voice agent that starts answering in about 0\.7 seconds/,
    );
  });

  test("its calls to action lead to a call and to the demo", async ({ page }) => {
    await openShowcase(page);

    const callLinks = page.getByRole("link", { name: "Call Kenji", exact: true });
    await expect(callLinks.first()).toBeVisible();
    for (const link of await callLinks.all()) {
      await expect(link).toHaveAttribute("href", "/#call");
    }
    await expect(page.getByRole("link", { name: "Watch a real call" })).toHaveAttribute(
      "href",
      "/?demo=1",
    );
  });

  test("the numbers count up to their real values", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await openShowcase(page);

    await scrollThrough(page);

    await expect(page.locator(".stat__value")).toHaveText(FINAL_STATS, {
      timeout: COUNT_UP_TIMEOUT_MS,
    });
  });

  test("never scrolls sideways at any supported width", async ({ page }) => {
    test.setTimeout(SIDEWAYS_SCROLL_TIMEOUT_MS);
    for (const width of WIDTHS) {
      await page.setViewportSize({ width, height: 900 });
      await openShowcase(page);
      await scrollThrough(page);

      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - window.innerWidth,
      );

      expect(overflow, `features page at ${String(width)}px`).toBeLessThanOrEqual(0);
    }
  });
});

test.describe("features page with reduced motion", () => {
  // With less motion nothing is animated, so every card must be shown as it is, not left hidden
  // in the start state of an animation that never runs. Axe also measures final colours this way.
  test.use({ reducedMotion: "reduce" });

  test("shows every X-ray card and every stack card without animating", async ({ page }) => {
    await openShowcase(page);

    await expectAllShown(page.locator(".xray-callout"), XRAY_CALLOUTS);
    await expectAllShown(page.locator(".stack-card"), STACK_CARDS);
  });

  test("passes a WCAG 2.1 AA scan", async ({ page }) => {
    await openShowcase(page);
    await scrollThrough(page);

    await expectNoAxeViolations(page);
  });
});
