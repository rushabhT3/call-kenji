import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { WIDTHS } from "./support.ts";

const PITCH_URL = "/pitch";
const WCAG_AA_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];
const STOPS = 9;
const LAST_STEP = 12;
// Long enough for the camera to finish a flight across the whole universe.
const FLIGHT_TIMEOUT_MS = 4000;

async function expectNoAxeViolations(page: Page): Promise<void> {
  const results = await new AxeBuilder({ page }).withTags(WCAG_AA_TAGS).analyze();
  const violations = results.violations.map(
    (violation) =>
      `${violation.id}: ${violation.nodes.map((node) => node.target.join(" ")).join(", ")}`,
  );
  expect(violations).toEqual([]);
}

async function openPitch(page: Page, hash = ""): Promise<void> {
  await page.goto(`${PITCH_URL}${hash}`);
  await expect(page.getByRole("heading", { level: 1, name: "Call Kenji!" })).toBeVisible();
}

async function expectStep(page: Page, step: number): Promise<void> {
  await expect(page).toHaveURL(step === 0 ? /\/pitch$/ : new RegExp(`/pitch#${String(step)}$`));
  await expect(page.locator(".pitch-bar__count")).toHaveText(
    `${String(step)} / ${String(LAST_STEP)}`,
  );
}

test.describe("pitch canvas", () => {
  test("opens on the map of the whole universe", async ({ page }) => {
    await openPitch(page);

    await expectStep(page, 0);
    await expect(page.getByRole("button", { name: "Start the pitch" })).toBeVisible();
  });

  test("the keyboard moves the camera on, back and home to the map", async ({ page }) => {
    await openPitch(page);

    await page.keyboard.press("ArrowRight");
    await expectStep(page, 1);
    await page.keyboard.press("ArrowRight");
    await expectStep(page, 2);
    await page.keyboard.press("ArrowLeft");
    await expectStep(page, 1);
    await page.keyboard.press("Home");
    await expectStep(page, 0);
  });

  test("a stop on the map is a door the camera flies through", async ({ page }) => {
    await openPitch(page);

    await page.getByRole("button", { name: "Fly to stop 3: The live X-ray" }).click();

    await expectStep(page, 3);
    await expect(page.getByRole("heading", { level: 2, name: "The live X-ray" })).toBeInViewport({
      timeout: FLIGHT_TIMEOUT_MS,
    });
  });

  test("a link opens the pitch at its step, with only that stop in reach", async ({ page }) => {
    await openPitch(page, "#9");

    await expectStep(page, 9);
    await expect(page.locator('[data-stop="rules"] section')).not.toHaveAttribute("inert");
    await expect(page.locator('[data-stop="stack"] section')).toHaveAttribute("inert");
  });

  test("never scrolls sideways at any supported width", async ({ page }) => {
    for (const width of WIDTHS) {
      await page.setViewportSize({ width, height: 900 });
      await openPitch(page, "#3");

      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - window.innerWidth,
      );

      expect(overflow, `sideways overflow at ${String(width)}px`).toBeLessThanOrEqual(0);
    }
  });
});

test.describe("pitch with reduced motion", () => {
  test.beforeEach(async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
  });

  test("reads as a page with every stop open", async ({ page }) => {
    await openPitch(page);
    const stops = page.locator(".pitch-stop section");

    await expect(stops).toHaveCount(STOPS);
    await expect(page.locator(".pitch-bar")).toHaveCount(0);
    for (const stop of await stops.all()) {
      await stop.scrollIntoViewIfNeeded();
      await expect(stop).toBeVisible();
      await expect(stop).not.toHaveAttribute("inert");
    }
  });

  test("passes a WCAG 2.1 AA scan", async ({ page }) => {
    await openPitch(page);

    await expectNoAxeViolations(page);
  });
});
