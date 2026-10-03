import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { WIDTHS } from "./support.ts";

const TRAILER_URL = "/trailer";
const VIDEO_FILE = "/trailer/kenji-trailer.mp4";
const VIDEO_PATTERN = `**${VIDEO_FILE}`;
const WCAG_AA_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];
const WAYS_ON = [
  { name: "Call Kenji", href: "/#call" },
  { name: "Explore Kenji's Universe", href: "/pitch" },
  { name: "How it's built", href: "/features" },
  { name: "Watch the demo call", href: "/?demo=1" },
] as const;

/** Holds the video request open, so the player waits for its first play whatever is on disk. */
async function holdVideo(page: Page): Promise<void> {
  await page.route(VIDEO_PATTERN, () => undefined);
}

async function failVideo(page: Page): Promise<void> {
  await page.route(VIDEO_PATTERN, (route) => route.fulfill({ status: 404, body: "" }));
}

async function openTrailer(page: Page): Promise<void> {
  await page.goto(TRAILER_URL);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
}

async function expectNoAxeViolations(page: Page): Promise<void> {
  const results = await new AxeBuilder({ page }).withTags(WCAG_AA_TAGS).analyze();
  const violations = results.violations.map(
    (violation) =>
      `${violation.id}: ${violation.nodes.map((node) => node.target.join(" ")).join(", ")}`,
  );
  expect(violations).toEqual([]);
}

test.describe("trailer page", () => {
  test("names itself and offers a way on after the credits", async ({ page }) => {
    await holdVideo(page);
    await openTrailer(page);

    await expect(page.getByRole("heading", { level: 1 })).toHaveText("Call Kenji: the trailer");
    const waysOn = page.getByRole("navigation", { name: "After the trailer" });
    for (const way of WAYS_ON) {
      await expect(waysOn.getByRole("link", { name: way.name, exact: true })).toHaveAttribute(
        "href",
        way.href,
      );
    }
  });

  test("plays the trailer from the site, behind a play button", async ({ page }) => {
    await holdVideo(page);
    await openTrailer(page);

    await expect(page.locator("video")).toHaveAttribute("src", VIDEO_FILE);
    await expect(page.getByRole("button", { name: "Play the trailer" })).toBeVisible();
  });

  test("shows a friendly card, not a broken player, when the video cannot load", async ({
    page,
  }) => {
    await failVideo(page);
    await openTrailer(page);

    await expect(
      page.getByRole("heading", { name: "The trailer is still rolling in" }),
    ).toBeVisible();
    await expect(page.locator("video")).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Try again" })).toBeVisible();
  });

  test("never scrolls sideways at any supported width", async ({ page }) => {
    await holdVideo(page);
    for (const width of WIDTHS) {
      await page.setViewportSize({ width, height: 900 });
      await openTrailer(page);

      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - window.innerWidth,
      );

      expect(overflow, `trailer page at ${String(width)}px`).toBeLessThanOrEqual(0);
    }
  });
});

test.describe("trailer page with reduced motion", () => {
  test.use({ reducedMotion: "reduce" });

  test("passes a WCAG 2.1 AA scan with the player waiting", async ({ page }) => {
    await holdVideo(page);
    await openTrailer(page);

    await expectNoAxeViolations(page);
  });

  test("passes a WCAG 2.1 AA scan with the friendly card", async ({ page }) => {
    await failVideo(page);
    await openTrailer(page);
    await expect(page.getByRole("button", { name: "Try again" })).toBeVisible();

    await expectNoAxeViolations(page);
  });
});
