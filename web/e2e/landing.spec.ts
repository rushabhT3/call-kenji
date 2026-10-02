import { expect, test } from "@playwright/test";

test("landing page names the product", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Call Kenji");
});
