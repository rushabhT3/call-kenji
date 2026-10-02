import { defineConfig, devices } from "@playwright/test";

const PREVIEW_PORT = 4173;
const PREVIEW_URL = `http://localhost:${String(PREVIEW_PORT)}`;
// A browser call asks for the microphone. Headless Chrome refuses every request unless it has a
// fake microphone and a fake permission prompt, which accepts.
const FAKE_MICROPHONE = {
  args: ["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"],
};

export default defineConfig({
  testDir: "./e2e",
  forbidOnly: Boolean(process.env.CI),
  reporter: process.env.CI ? "github" : "list",
  use: { baseURL: PREVIEW_URL },
  webServer: {
    command: `npm run build && npm run preview -- --port ${String(PREVIEW_PORT)} --strictPort`,
    url: PREVIEW_URL,
    reuseExistingServer: !process.env.CI,
  },
  projects: [
    {
      name: "desktop-1440",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1440, height: 900 },
        launchOptions: FAKE_MICROPHONE,
      },
    },
    {
      name: "mobile-390",
      use: {
        ...devices["Pixel 7"],
        viewport: { width: 390, height: 844 },
        launchOptions: FAKE_MICROPHONE,
      },
    },
  ],
});
