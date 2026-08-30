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

test("demo exercises two synthetic pets with five observations each", async ({ page }) => {
  await page.goto("/?demo=1#SCAN");
  const picker = page.locator("#file-picker");
  const pets = [
    { id: "demo-luna", name: "Luna", files: ["luna-healthy-01.png", "luna-healthy-02.png", "luna-healthy-03.png", "luna-healthy-04.png", "luna-healthy-05.png"] },
    { id: "demo-max", name: "Max", files: ["max-unhealthy-01.png", "max-unhealthy-02.png", "max-unhealthy-03.png", "max-unhealthy-04.png", "max-unhealthy-05.png"] },
  ];
  for (const pet of pets) {
    await page.evaluate((value) => { window.PETI_STATE.selectedPet = value; }, { id: pet.id, display_name: pet.name, species: "DOG" });
    for (const file of pet.files) {
      await picker.setInputFiles(path.resolve(process.cwd(), "tests/fixtures/dogs", file));
      await expect(page.locator("#scan-status")).toContainText(file);
    }
  }
});
