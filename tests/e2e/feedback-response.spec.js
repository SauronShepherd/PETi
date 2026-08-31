import { test, expect } from "@playwright/test";

test("demo feedback can be edited and removed without backend writes", async ({ page }) => {
  const writes = [];
  page.on("request", request => {
    if (request.url().includes("/v1/agent-runs") && request.method() !== "GET") writes.push(request.url());
  });
  await page.goto("/?demo=1#AGENTS");
  await page.getByRole("button", { name: "Iniciar revisión" }).click();
  await expect(page.getByText(/Estado: COMPLETED/)).toBeVisible();
  await page.getByRole("button", { name: "Sí, me ayudó" }).click();
  await page.locator("#agent-feedback-reason").selectOption("CLEAR");
  await page.getByRole("button", { name: "Enviar valoración" }).click();
  await page.getByRole("button", { name: "Cambiar valoración" }).click();
  await page.getByRole("button", { name: "No del todo" }).click();
  await page.locator("#agent-feedback-reason").selectOption("TOO_GENERIC");
  await page.getByRole("button", { name: "Enviar valoración" }).click();
  await expect(page.getByText(/Demasiado genérico/)).toBeVisible();
  await page.getByRole("button", { name: "Retirar valoración" }).click();
  await expect(page.getByText("¿Te ha ayudado esta respuesta?")).toBeVisible();
  expect(await page.evaluate(() => sessionStorage.getItem("peti.lab.demo.feedback.demo-response-demo-luna"))).toBeNull();
  expect(writes).toEqual([]);
});

test("completed analysis feedback is contextual and remains local in demo", async ({ page }) => {
  const writes = [];
  page.on("request", request => {
    if (request.url().includes("/v1/agent-runs") && request.method() !== "GET") writes.push(request.url());
  });
  await page.goto("/?demo=1#SCAN");
  await page.evaluate(() => {
    window.PETI_STATE.analysis = {
      id: "demo-analysis-luna",
      response_id: "demo-analysis-response-luna",
      status: "COMPLETED",
      result: { structured_payload: { observations: [{ text: "Pelaje uniforme en la imagen." }] } },
    };
    window.PETI_RENDER();
  });
  await expect(page.getByText("Pelaje uniforme en la imagen.")).toBeVisible();
  await page.getByRole("button", { name: "Sí, me ayudó" }).click();
  await page.locator("#analysis-feedback-reason").selectOption("USED_EVIDENCE_WELL");
  await page.locator("#analysis-feedback-comment").fill("La procedencia queda clara.");
  await page.locator("#analysis-feedback-form").getByRole("button", { name: "Enviar valoración" }).click();
  await expect(page.getByText("Gracias por valorar este análisis")).toBeVisible();
  const stored = await page.evaluate(() => sessionStorage.getItem("peti.lab.demo.feedback.demo-analysis-response-luna"));
  expect(stored).toContain("USED_EVIDENCE_WELL");
  expect(writes).toEqual([]);
});
