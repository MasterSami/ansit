import { existsSync } from "node:fs";

import { defineConfig } from "@playwright/test";

const PORT = 3100;
// Some sandboxes ship a system Chromium instead of Playwright's download.
const localChromium = "/opt/pw-browsers/chromium";

export default defineConfig({
  testDir: "tests/e2e",
  timeout: 60_000,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: `http://localhost:${PORT}`,
    locale: "ar",
    viewport: { width: 402, height: 874 },
    launchOptions: {
      ...(existsSync(localChromium) ? { executablePath: localChromium } : {}),
      // A synthetic microphone, so the real recording path runs without hardware.
      args: [
        "--use-fake-ui-for-media-stream",
        "--use-fake-device-for-media-stream",
      ],
    },
  },
  webServer: {
    command: `npm run build && npm run start -- --port ${PORT}`,
    url: `http://localhost:${PORT}`,
    timeout: 240_000,
    reuseExistingServer: !process.env.CI,
  },
});
