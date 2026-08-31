import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const output = path.join(process.cwd(), "release", "evidence", "navigation", "screenshots-en");
await mkdir(output, { recursive: true });
const server = (await import("node:child_process")).spawn("python", ["-m", "http.server", "4173", "--bind", "127.0.0.1", "-d", "web"], { stdio: "ignore" });
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await context.newPage();
const base = "http://127.0.0.1:4173/?demo=1&lang=en";
const shot = async (name) => page.screenshot({ path: path.join(output, name), fullPage: true });

try {
  await page.goto(`${base}#HOME`); await shot("01-user-home.png");
  await page.goto(`${base}#AGENTS`); await shot("02-user-agents.png");
  await page.getByRole("button", { name: "Start review" }).click(); await page.waitForTimeout(1200); await shot("03-user-agent-result.png");
  await page.goto(`${base}#CARE`); await shot("04-user-care.png");
  await page.goto(`${base}#RECORDS`); await shot("05-user-evidence-records.png");

  await page.goto(`${base}#ADMIN`); await page.getByRole("button", { name: /Agent Laboratory/ }).click(); await shot("06-admin-agent-laboratory.png");
  await page.getByRole("button", { name: /Model Intelligence/ }).click(); await shot("07-admin-model-intelligence.png");
  await page.getByRole("button", { name: /Live Runs/ }).click(); await shot("08-admin-live-runs.png");
  await page.getByRole("button", { name: "demo-run-max" }).click(); await shot("09-admin-run-trace.png");
  await page.getByRole("tab", { name: "Evidence & claims" }).click(); await shot("10-admin-evidence-claims.png");
} finally {
  await context.close(); await browser.close(); server.kill();
}
console.log(`SCREENSHOTS_READY=${output}`);
