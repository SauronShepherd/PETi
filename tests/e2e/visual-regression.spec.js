import { test, expect } from "@playwright/test";
import path from "node:path";

const routes = ["HOME", "SCAN", "HISTORY", "PROFILE", "AGENTS", "CARE", "BODY_CHECK", "RECORDS", "ASSISTANT", "PLANS", "SETTINGS", "FEEDBACK", "COLLABORATION", "LIBRARY", "ADMIN"];
const fixture = path.resolve(process.cwd(), "tests/fixtures/golden-retriever.jpg");

for (const route of routes) {
  test(`visual baseline ${route}`, async ({ page }) => {
    await page.goto(`/?demo=1#${route}`);
    await expect(page.locator("#app")).toBeVisible();
    await expect(page).toHaveScreenshot(`${route.toLowerCase()}.png`, {
      fullPage: true,
      animations: "disabled",
      caret: "hide",
      scale: "css",
      maxDiffPixelRatio: 0.01,
    });
  });
}

test("golden retriever fixture loads and is accepted by the demo image flow", async ({ page }) => {
  await page.goto("/?demo=1#SCAN");
  const picker = page.locator("#file-picker");
  await page.getByRole("button", { name: /Foto/ }).click();
  await picker.setInputFiles(fixture);
  await expect(page.locator("#scan-status")).toContainText("golden-retriever.jpg");
  const image = await page.evaluate(async () => {
    const response = await fetch("/assets/login-comic-background.png");
    const blob = await response.blob();
    return { type: blob.type, size: blob.size };
  });
  expect(image.type).toMatch(/^image\//);
  expect(image.size).toBeGreaterThan(1000);
});
