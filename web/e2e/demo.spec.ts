import { expect, test } from "@playwright/test";
import {
  DEMO_URL,
  WIDTHS,
  blockBackend,
  openAfterCall,
  openMidCall,
  serveMeasuredRecording,
} from "./support.ts";

const SIDEWAYS_SCROLL_TIMEOUT_MS = 120_000;

test.describe("demo replay", () => {
  test("replays a whole call with no backend at all", async ({ page }) => {
    const attempts = await blockBackend(page);
    await page.goto(DEMO_URL);

    await expect(page.getByText("Demo replay")).toBeVisible();
    await expect(page.getByRole("heading", { name: /What happened/ })).toBeVisible({
      timeout: 20_000,
    });
    expect(attempts).toEqual([]);
  });

  test("shows every card of the X-ray", async ({ page }) => {
    await blockBackend(page);
    await page.goto(DEMO_URL);
    await expect(page.getByRole("heading", { name: /What happened/ })).toBeVisible({
      timeout: 20_000,
    });

    const log = page.getByRole("log");
    await expect(log.getByRole("listitem").first()).toBeVisible();
    await expect(log.locator('[lang="en"]').first()).not.toBeEmpty();
    await expect(page.locator("#compliance")).toContainText("safeguards holding");
    await expect(page.locator("#strategist")).toContainText("Identity");
    await expect(page.locator("#turn")).toBeVisible();
    await expect(page.locator("#latency")).toBeVisible();
    await expect(page.locator("#sms")).toContainText("Not sent");
    await expect(page.locator("#handoff")).toBeVisible();
    await expect(page.locator("#audit")).toContainText("Hash chain verified");
  });

  test("copies the audit record as valid JSON", async ({ page, context, browserName }) => {
    test.skip(browserName !== "chromium", "clipboard permissions are Chromium-only here");
    await context.grantPermissions(["clipboard-read", "clipboard-write"]);
    await blockBackend(page);
    await page.goto(DEMO_URL);

    await page.getByRole("button", { name: "Copy JSON" }).click({ timeout: 20_000 });

    await expect(page.getByRole("button", { name: "Copied" })).toBeVisible();
    const copied = await page.evaluate(() => navigator.clipboard.readText());
    const records = JSON.parse(copied) as { hash: string }[];
    expect(records.length).toBeGreaterThan(5);
    expect(records.every((record) => /^[0-9a-f]{64}$/.test(record.hash))).toBe(true);
  });

  test("never scrolls sideways at any supported width", async ({ page }) => {
    test.setTimeout(SIDEWAYS_SCROLL_TIMEOUT_MS);
    await blockBackend(page);
    await serveMeasuredRecording(page);
    const states = [
      {
        name: "landing",
        open: async () => {
          await page.goto("/");
          await page.waitForLoadState("networkidle");
        },
      },
      { name: "live view mid-call", open: () => openMidCall(page) },
      { name: "after the call", open: () => openAfterCall(page) },
    ];
    for (const width of WIDTHS) {
      await page.setViewportSize({ width, height: 900 });
      for (const state of states) {
        await state.open();
        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth - window.innerWidth,
        );
        expect(overflow, `${state.name} at ${String(width)}px`).toBeLessThanOrEqual(0);
      }
    }
  });
});
