import { expect, test } from "@playwright/test";
import { blockBackend, routeViewerFeed, sendViewerReady } from "./support.ts";

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

test("a refreshed link code replaces the old one and keeps the call button ready", async ({
  page,
}) => {
  const feed = await routeViewerFeed(page);
  await page.goto("/");
  const socket = await feed.connected;

  sendViewerReady(socket, "4821");
  await expect(page.getByRole("group", { name: "Your code: 4 8 2 1" })).toBeVisible();

  sendViewerReady(socket, "0937");
  await expect(page.getByRole("group", { name: "Your code: 0 9 3 7" })).toBeVisible();
  await expect(page.getByRole("group", { name: "Your code: 4 8 2 1" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Call from browser" })).toHaveAttribute(
    "aria-disabled",
    "false",
  );
});

test("a call Kenji could not hear is never placed", async ({ page }) => {
  await page.addInitScript(() => {
    navigator.mediaDevices.getUserMedia = () =>
      Promise.reject(new DOMException("Permission denied", "NotAllowedError"));
  });
  const feed = await routeViewerFeed(page);
  const offers: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("/api/offer")) {
      offers.push(request.url());
    }
  });
  await page.goto("/");
  sendViewerReady(await feed.connected, "4821");

  await page.getByRole("button", { name: "Call from browser" }).click();

  await expect(page.locator(".call-panel__error")).toContainText("blocked the microphone");
  expect(offers).toEqual([]);
});

test("an unreachable line is explained in plain words", async ({ page }) => {
  const feed = await routeViewerFeed(page);
  await page.goto("/");
  sendViewerReady(await feed.connected, "4821");

  await page.getByRole("button", { name: "Call from browser" }).click();

  await expect(page.locator(".call-panel__error")).toHaveText(
    "Kenji's line can't be reached right now. Please try again in a minute.",
  );
});
