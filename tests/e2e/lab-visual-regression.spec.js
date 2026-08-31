import { test, expect } from "@playwright/test";

test("Veterinary AI Lab command center visual baseline", async ({ page }) => {
  await page.goto("/?demo=1#ADMIN");
  await expect(page.locator(".peti-lab")).toHaveScreenshot("lab-command-center.png", { animations: "disabled" });
});

test("Veterinary AI Lab run inspector visual baseline", async ({ page }) => {
  await page.goto("/?demo=1#ADMIN");
  await page.getByRole("button", { name: /Live Runs/ }).click();
  await page.getByRole("button", { name: "demo-run-max" }).click();
  await expect(page.locator(".lab-main")).toHaveScreenshot("lab-run-max.png", { animations: "disabled" });
});

test("Veterinary AI Lab model, feedback and safety views remain stable", async ({ page }) => {
  await page.goto("/?demo=1#ADMIN");
  for (const [name, file] of [[/Model Intelligence/, "lab-models.png"], [/User Feedback/, "lab-feedback.png"], [/Safety & Evals/, "lab-safety.png"]]) {
    await page.getByRole("button", { name }).click();
    await expect(page.locator(".lab-main")).toHaveScreenshot(file, { animations: "disabled" });
  }
});
