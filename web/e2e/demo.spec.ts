import { expect, test } from "@playwright/test";
import { DEMO_URL, WIDTHS, blockBackend, openAfterCall, openMidCall } from "./support.ts";

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

  test("offers a call of your own throughout the replay", async ({ page }) => {
    await blockBackend(page);
    await openMidCall(page);

    const banner = page.getByRole("complementary", { name: "About this replay" });
    await expect(banner.getByRole("link", { name: "Call Kenji yourself" })).toHaveAttribute(
      "href",
      "/#call",
    );
    await expect(banner.getByRole("link", { name: "Home" })).toHaveAttribute("href", "/");
  });

  test("ends with a way to call, to watch again and to go home", async ({ page }) => {
    await blockBackend(page);
    await openAfterCall(page);

    const next = page.getByRole("navigation", { name: "What next" });
    await expect(next.getByRole("link", { name: "Call Kenji yourself" })).toHaveAttribute(
      "href",
      "/#call",
    );
    await expect(next.getByRole("link", { name: "Watch again" })).toHaveAttribute(
      "href",
      "/?demo=1",
    );
    await expect(next.getByRole("link", { name: "Home" })).toHaveAttribute("href", "/");
  });

  test("a live transcript keeps to the latest lines, the rest one press away", async ({ page }) => {
    await blockBackend(page);
    await openMidCall(page);

    const earlier = page.getByRole("button", { name: /^Show \d+ earlier lines?$/ });
    await earlier.click({ timeout: 20_000 });

    await expect(page.getByRole("button", { name: "Show the latest lines only" })).toBeVisible();
    await expect(page.getByRole("log").getByRole("listitem").nth(3)).toBeVisible();
  });

  test("the audit record reads as a timeline, the raw JSON one press away", async ({ page }) => {
    await blockBackend(page);
    await openAfterCall(page);
    const audit = page.locator("#audit");

    await expect(audit.getByRole("list", { name: /step by step/ })).toContainText(
      "Payment promise recorded",
    );
    await audit.getByRole("button", { name: "Show raw JSON" }).click();

    await expect(audit.getByLabel("Audit record JSON")).toContainText("previous_hash");
  });

  test("a summary chip lands its card below the sticky bars", async ({ page }) => {
    await blockBackend(page);
    await openAfterCall(page);
    const chip = page.getByRole("link", { name: /^Compliance/ });
    test.skip(!(await chip.isVisible()), "summary chips are shown on narrow screens only");

    await page.evaluate(() => {
      window.scrollTo(0, 0);
    });
    await chip.click();

    const title = page.locator("#compliance .card__title");
    await expect(title).toBeInViewport();
    const isUncovered = await title.evaluate((element) => {
      const box = element.getBoundingClientRect();
      const topmost = document.elementFromPoint(box.left + 1, box.top + box.height / 2);
      return topmost !== null && element.contains(topmost);
    });
    expect(isUncovered).toBe(true);
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
