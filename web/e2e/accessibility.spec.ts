import { expect, test } from "@playwright/test";
import { DEMO_URL, blockBackend } from "./support.ts";

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

  test("numbers use tabular figures", async ({ page }) => {
    await blockBackend(page);
    await page.goto("/");

    const numeric = await page
      .locator(".role__value")
      .first()
      .evaluate((element) => getComputedStyle(element).fontVariantNumeric);
    expect(numeric).toContain("tabular-nums");
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
