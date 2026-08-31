import { test, expect } from "@playwright/test";

test("Lab navigation exposes state, focus and landmarks", async ({ page }) => {
  await page.goto("/?demo=1#ADMIN");
  await expect(page.locator("aside[aria-label='Veterinary AI Lab']")).toBeVisible();
  const command = page.getByRole("button", { name: /Command Center/ });
  await expect(command).toHaveAttribute("aria-current", "page");
  const runs = page.getByRole("button", { name: /Live Runs/ });
  await runs.focus();
  await page.keyboard.press("Enter");
  await expect(runs).toHaveAttribute("aria-current", "page");
  await expect(page.locator(".lab-main")).toBeFocused();
  await expect(page.getByRole("heading", { level: 1, name: "Agent runs" })).toBeVisible();
});

test("Lab mobile has no document-level horizontal overflow and honors reduced motion", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/?demo=1#ADMIN");
  const dimensions = await page.evaluate(() => ({ width: document.documentElement.scrollWidth, viewport: document.documentElement.clientWidth }));
  expect(dimensions.width).toBeLessThanOrEqual(dimensions.viewport);
  const duration = await page.locator(".lab-loading i").evaluateAll(nodes => nodes[0] ? getComputedStyle(nodes[0]).animationDuration : "0.01ms");
  expect(["0s", "0.01ms"]).toContain(duration);
});

test("every Lab view has complete English copy coverage", async ({ page }) => {
  await page.goto("/?demo=1&lang=en#ADMIN/COMMAND_CENTER");
  const views = ["Live Runs", "Agent Laboratory", "Model Intelligence", "Evidence Lab", "User Feedback", "Safety & Evals", "Performance & Cost", "System Health", "Audit & Governance", "Command Center"];
  for (const name of views) {
    await page.getByRole("button", { name: new RegExp(name) }).click();
    const copy = await page.locator(".lab-main").innerText();
    expect(copy).not.toMatch(/\b(Sin|Dónde|Abrir|Seguridad|Actividad|Resultado|Llamadas|Esta|Ningún|Coste|Todavía|Aún|Datos|Comprueba|muestra|evidencias)\b/i);
  }
});
