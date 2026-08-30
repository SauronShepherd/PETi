import { test, expect } from "@playwright/test";

const routes = ["HOME", "SCAN", "HISTORY", "PROFILE", "AGENTS", "CARE", "BODY_CHECK", "RECORDS", "ASSISTANT", "PLANS", "SETTINGS", "FEEDBACK", "COLLABORATION", "LIBRARY", "ADMIN"];

for (const route of routes) {
  test(`${route} renders without layout or asset regressions`, async ({ page }, testInfo) => {
    const consoleErrors = [];
    page.on("console", (message) => { if (message.type() === "error") consoleErrors.push(message.text()); });
    await page.goto(`/?demo=1#${route}`);
    await expect(page.locator("#app")).toBeVisible();
    await expect(page.locator("body")).not.toContainText("<div");
    const diagnostic = await page.evaluate(() => ({
      viewport: { width: innerWidth, height: innerHeight },
      overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      brokenImages: [...document.images].filter((image) => !image.complete || image.naturalWidth === 0).length,
      buttons: [...document.querySelectorAll("button")].map((button) => ({ text: button.textContent.trim(), disabled: button.disabled })),
    }));
    await page.screenshot({ path: testInfo.outputPath(`${route.toLowerCase()}-${testInfo.project.name}.png`), fullPage: true });
    expect(diagnostic.overflowX).toBeLessThanOrEqual(0);
    expect(diagnostic.brokenImages).toBe(0);
    expect(consoleErrors).toEqual([]);
  });
}
