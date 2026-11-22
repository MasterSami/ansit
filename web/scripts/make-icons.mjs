// Renders public/icons/icon.svg to the PNG sizes the manifest needs.
// Usage: node scripts/make-icons.mjs   (needs Playwright's Chromium)
import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { chromium } from "@playwright/test";

const dir = fileURLToPath(new URL("../public/icons/", import.meta.url));
const svg = readFileSync(`${dir}icon.svg`, "utf8");
// Maskable icons are cropped by the OS, so the background must reach the edges.
const maskable = svg.replace('rx="96"', 'rx="0"');

const local = "/opt/pw-browsers/chromium";
const browser = await chromium.launch(
  existsSync(local) ? { executablePath: local } : {},
);
const page = await browser.newPage();
for (const [name, size, source] of [
  ["icon-192.png", 192, svg],
  ["icon-512.png", 512, svg],
  ["icon-maskable-512.png", 512, maskable],
  ["apple-touch-icon.png", 180, maskable],
]) {
  await page.setViewportSize({ width: size, height: size });
  await page.setContent(
    `<style>*{margin:0}svg{display:block;width:${size}px;height:${size}px}</style>${source}`,
  );
  await page.screenshot({ path: `${dir}${name}`, omitBackground: true });
}
await browser.close();
