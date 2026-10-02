import { expect, test } from "@playwright/test";
import { blockBackend } from "./support.ts";

test("landing page shows the role card and both ways to call", async ({ page }) => {
  await blockBackend(page);
  await page.goto("/");

  await expect(page.getByRole("heading", { level: 1 })).toContainText("Call Kenji.");
  await expect(page.getByRole("heading", { name: /佐藤ゆうき/ })).toBeVisible();
  await expect(page.getByText("¥35,000")).toBeVisible();
  await expect(page.getByRole("button", { name: "Call from browser" })).toBeVisible();
  await expect(page.getByText("Audio is never stored")).toBeVisible();
});

test("browser call stays disabled until this tab has its private feed", async ({ page }) => {
  await blockBackend(page);
  await page.goto("/");

  await expect(page.getByRole("button", { name: "Call from browser" })).toHaveAttribute(
    "aria-disabled",
    "true",
  );
});
