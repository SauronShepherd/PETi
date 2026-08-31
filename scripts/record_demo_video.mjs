import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { spawn } from "node:child_process";
import path from "node:path";

const root = process.cwd();
const outputDir = path.join(root, "release", "evidence", "navigation");
await mkdir(outputDir, { recursive: true });
const server = spawn("python", ["-m", "http.server", "4173", "--bind", "127.0.0.1", "-d", "web"], {
  cwd: root,
  stdio: "ignore",
});
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  recordVideo: { dir: outputDir, size: { width: 1440, height: 900 } },
});
const page = await context.newPage();
const pause = (ms = 1200) => page.waitForTimeout(ms);

try {
  await page.goto("http://127.0.0.1:4173/?demo=1#HOME");
  await pause(1800);
  await page.goto("http://127.0.0.1:4173/?demo=1#AGENTS");
  await pause(1800);
  await page.getByRole("button", { name: "Iniciar revisión" }).click();
  await pause(5200);
  await page.goto("http://127.0.0.1:4173/?demo=1#ADMIN");
  await pause(1800);
  await page.getByRole("button", { name: /Agent Laboratory/ }).click();
  await pause(2200);
  await page.getByRole("button", { name: /Model Intelligence/ }).click();
  await pause(2200);
  await page.getByRole("button", { name: /Live Runs/ }).click();
  await pause(2200);
  await page.getByRole("button", { name: "demo-run-max" }).click();
  await pause(2200);
  await page.getByRole("tab", { name: "Evidence & claims" }).click();
  await pause(2200);
  await page.getByRole("tab", { name: "Models & tools" }).click();
  await pause(2200);
  await page.getByRole("tab", { name: "Versions" }).click();
  await pause(2600);
} finally {
  await context.close();
  await browser.close();
  server.kill();
}

console.log("VIDEO_READY");
