import type { Page } from "@playwright/test";

/** Abort every request to the voice server so a test proves the page needs no backend. */
export async function blockBackend(page: Page): Promise<string[]> {
  const attempts: string[] = [];
  await page.route(/\/(api|ws|start|sessions)\b/, async (route) => {
    attempts.push(route.request().url());
    await route.abort();
  });
  await page.routeWebSocket(/.*/, (socket) => {
    attempts.push(socket.url());
    void socket.close();
  });
  return attempts;
}

export const DEMO_URL = "/?demo=1&speed=4";
export const WIDTHS = [1440, 1024, 768, 390] as const;
