import { expect, test, type Page } from "@playwright/test";
import { blockBackend, captureOffers, routeViewerFeed, sendViewerReady } from "./support.ts";

const personaPicker = (page: Page) => page.getByRole("group", { name: /Choose who you play/ });

test("landing page shows the role card and both ways to call", async ({ page }) => {
  await blockBackend(page);
  await page.goto("/");

  await expect(page.getByRole("heading", { level: 1 })).toContainText("Call Kenji.");
  await expect(page.getByRole("heading", { name: /佐藤ゆうき/ })).toBeVisible();
  await expect(page.getByText("¥35,000")).toBeVisible();
  await expect(page.getByRole("button", { name: "Call from browser" })).toBeVisible();
  await expect(page.getByText("Audio is never stored")).toBeVisible();
});

test("the picker offers five people to play, and choosing one shows their facts", async ({
  page,
}) => {
  await blockBackend(page);
  await page.goto("/");
  const picker = personaPicker(page);
  await expect(picker.getByRole("radio")).toHaveCount(5);
  await expect(picker.getByRole("radio", { name: /佐藤ゆうき/ })).toBeChecked();

  await picker.getByRole("radio", { name: /田中けんた/ }).check();

  await expect(page.getByRole("heading", { name: /田中けんた/ })).toBeVisible();
  await expect(page.getByText("¥52,000")).toBeVisible();
  await expect(page.getByText("昭和60年3月2日", { exact: true })).toBeVisible();
  await expect(page.getByText("4410", { exact: true })).toBeVisible();
  await expect(page.getByText("¥35,000")).toHaveCount(0);
});

test("Surprise me picks someone else, and the page remembers the choice", async ({ page }) => {
  await blockBackend(page);
  await page.goto("/");
  const picker = personaPicker(page);
  await expect(picker.getByRole("radio", { name: /佐藤ゆうき/ })).toBeChecked();

  await picker.getByRole("button", { name: "Surprise me" }).click();

  await expect(picker.getByRole("radio", { name: /佐藤ゆうき/ })).not.toBeChecked();
  const chosen = await picker.getByRole("radio", { checked: true }).getAttribute("value");
  await page.reload();
  await expect(picker.getByRole("radio", { checked: true })).toHaveAttribute("value", chosen ?? "");
});

test("a browser call tells the server who the caller plays", async ({ page }) => {
  const feed = await routeViewerFeed(page);
  const offers = await captureOffers(page);
  await page.goto("/");
  sendViewerReady(await feed.connected, "4821");
  await personaPicker(page)
    .getByRole("radio", { name: /鈴木はるか/ })
    .check();

  await page.getByRole("button", { name: "Call from browser" }).click();

  // Asking the browser for its devices can take a few seconds on a busy machine.
  await expect
    .poll(() => offers[0], { timeout: 15_000 })
    .toMatchObject({ requestData: { viewer_id: "viewer-1", persona_id: "suzuki" } });
});

test("without the list of roles, the page still calls as the default role", async ({ page }) => {
  await page.route("**/personas.json", (route) => route.abort());
  const feed = await routeViewerFeed(page);
  const offers = await captureOffers(page);
  await page.goto("/");
  sendViewerReady(await feed.connected, "4821");

  await expect(page.getByRole("alert")).toContainText("The roles didn't load");
  await expect(page.getByRole("group", { name: /Choose who you play/ })).toHaveCount(0);
  await page.getByRole("button", { name: "Call from browser" }).click();

  await expect
    .poll(() => offers[0], { timeout: 15_000 })
    .toMatchObject({ requestData: { persona_id: "sato" } });
});

test("the header leads to the explainer and the demo at every width", async ({ page }) => {
  await blockBackend(page);
  await page.goto("/");

  await expect(
    page.getByRole("link", { name: /How to read the X-ray|How it works/ }),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: /Watch a demo call|Demo/ })).toBeVisible();
  await expect(page.getByRole("link", { name: /home/ })).toHaveAttribute("href", "/");
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

  // Asking the browser for its devices can take a few seconds on a busy machine.
  await expect(page.locator(".call-panel__error")).toContainText("blocked the microphone", {
    timeout: 15_000,
  });
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
