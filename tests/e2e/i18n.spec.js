import { test, expect } from "@playwright/test";

test("English mode translates the public demo and agent workflow", async ({ page }) => {
  await page.goto("/?demo=1&lang=en#HOME");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page).toHaveTitle("PETi — Your companion. Our care.");
  await expect(page.getByRole("heading", { name: "Everything important, today." })).toBeVisible();
  await expect(page.getByText("Select a pet to explore its evidence.")).toBeVisible();
  await page.evaluate(() => { location.hash = "AGENTS"; });
  await expect(page.getByRole("heading", { name: "Multi-agent workflow" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Start review" })).toBeVisible();
  await expect(page.locator("body")).not.toContainText(/Inicio|Selecciona una mascota|Flujo multi-agente|Iniciar revisión/);
});

test("English mode covers every public demo route", async ({ page }) => {
  const routes = ["HOME", "SCAN", "HISTORY", "PROFILE", "AGENTS", "CARE", "BODY_CHECK", "RECORDS", "ASSISTANT", "PLANS", "SETTINGS", "FEEDBACK", "COLLABORATION", "LIBRARY", "ADMIN"];
  const untranslated = /Analizar y entender|Elige una evidencia|Todo en orden|Perfil registrado|Acceso restringido|Inicia sesión|Sin registros|No es un diagnóstico/;
  for (const route of routes) {
    await page.goto(`/?demo=1&lang=en&route=${route}#${route}`);
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
    await expect(page.locator("main")).not.toContainText(untranslated);
  }
});
