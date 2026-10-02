import { expect, test } from "@playwright/test";
import { mkdirSync } from "node:fs";
import path from "node:path";
import { blockBackend } from "./support.ts";

const SCREENSHOT_DIR = path.resolve(import.meta.dirname, "../../docs/screenshots");

test.describe("screenshots", () => {
  test.beforeAll(() => {
    mkdirSync(SCREENSHOT_DIR, { recursive: true });
  });

  test("before, during and after a call", async ({ page }, testInfo) => {
    await blockBackend(page);
    const width = page.viewportSize()?.width ?? 0;
    const shot = (name: string) =>
      page.screenshot({
        path: path.join(SCREENSHOT_DIR, `${name}-${String(width)}.png`),
        fullPage: true,
      });

    await page.goto("/");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await shot("before-call");

    await page.goto("/?demo=1&speed=0.25");
    await expect(page.getByRole("log").getByRole("listitem").nth(3)).toBeVisible();
    await shot("live");

    await expect(page.getByRole("heading", { name: /What happened/ })).toBeVisible({
      timeout: 20_000,
    });
    await shot("after-call");
    testInfo.annotations.push({ type: "screenshots", description: SCREENSHOT_DIR });
  });
});
