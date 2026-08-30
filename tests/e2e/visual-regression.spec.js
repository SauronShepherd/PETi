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

test("visual baseline Max evidence", async ({ page }) => {
  await page.goto("/?demo=1#HOME");
  await page.locator('[data-demo-pet="demo-max"]').click();
  const panel = page.locator("#demo-pets");
  await expect(panel).toContainText(/(?:Evidence for|Evidencias de) Max:/);
  await expect(panel).toHaveScreenshot("max-evidence.png", {
    animations: "disabled",
    caret: "hide",
    scale: "css",
    maxDiffPixelRatio: 0.01,
  });
});

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

test("demo exercises two synthetic pets with five observations each", async ({ page }) => {
  await page.goto("/?demo=1#SCAN");
  const picker = page.locator("#file-picker");
  const pets = [
    { id: "demo-luna", name: "Luna", files: ["luna-healthy-01.jpg", "luna-healthy-02.jpg", "luna-healthy-03.jpg", "luna-healthy-04.jpg", "luna-healthy-05.jpg"] },
    { id: "demo-max", name: "Max", files: ["max-unhealthy-01.jpg", "max-unhealthy-02.jpg", "max-unhealthy-03.jpg", "max-unhealthy-04.jpg", "max-unhealthy-05.jpg"] },
  ];
  for (const pet of pets) {
    await page.evaluate((value) => { window.PETI_STATE.selectedPet = value; }, { id: pet.id, display_name: pet.name, species: "DOG" });
    for (const file of pet.files) {
      await picker.setInputFiles(path.resolve(process.cwd(), "tests/fixtures/dogs", file));
      await expect(page.locator("#scan-status")).toContainText(file);
    }
  }
});
