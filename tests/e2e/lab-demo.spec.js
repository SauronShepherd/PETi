import { test, expect } from "@playwright/test";

test("Veterinary AI Lab demo exposes a labelled multi-agent mission control", async ({ page }) => {
  const backendRequests = [];
  page.on("request", (request) => {
    if (request.url().includes("/v1/internal/lab")) backendRequests.push(request.url());
  });
  await page.goto("/?demo=1#ADMIN");
  await expect(page.getByText("PETi Veterinary AI Lab", { exact: true })).toBeVisible();
  await expect(page.getByText("Synthetic replay · no representa usuarios ni tráfico real")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Multi-Agent Mission Control" })).toBeVisible();
  await expect(page.locator(".lab-rufs strong").first()).toContainText("78");
  expect(backendRequests).toEqual([]);
});

test("Lab demo navigates through agents, models, feedback and run trace", async ({ page }) => {
  await page.goto("/?demo=1#ADMIN");
  await page.getByRole("button", { name: /Agent Laboratory/ }).click();
  await expect(page).toHaveURL(/#ADMIN\/AGENTS$/);
  await expect(page.getByRole("heading", { name: "Agent Laboratory" })).toBeVisible();
  await expect(page.getByText("SAFETY_REVIEW", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: /Model Intelligence/ }).click();
  await expect(page).toHaveURL(/#ADMIN\/MODELS$/);
  await expect(page.getByText("gemini-3.5-flash", { exact: true })).toBeVisible();
  await expect(page.getByText("gemini-2.5-flash", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: /User Feedback/ }).click();
  await page.getByRole("button", { name: "Abrir traza →" }).first().click();
  await expect(page).toHaveURL(/#ADMIN\/RUNS\/demo-run-max$/);
  await expect(page.getByRole("heading", { name: "demo-run-max" })).toBeVisible();
  await expect(page.getByText("Sin siguiente paso claro")).toBeVisible();
  await expect(page.getByText("PET_SPECIALIST", { exact: true })).toBeVisible();
  await page.getByRole("tab", { name: "Evidence & claims" }).click();
  await expect(page.getByRole("heading", { name: "Evidence & claims" })).toBeVisible();
  await expect(page.getByText(/evidence-intake · IMAGE/)).toBeVisible();
  await page.getByRole("tab", { name: "Models & tools" }).click();
  await expect(page.getByText("gemini-3.5-flash", { exact: true })).toBeVisible();
  await expect(page.getByText("evidence-catalog", { exact: true })).toBeVisible();
  await page.getByRole("tab", { name: "Versions" }).click();
  await expect(page.getByText(/gemini-3.5-flash/)).toBeVisible();
  await page.goBack();
  await expect(page.getByRole("heading", { name: "User Experience & Feedback" })).toBeVisible();
});

test("agent response feedback is contextual, editable and local in demo", async ({ page }) => {
  await page.goto("/?demo=1#AGENTS");
  await page.getByRole("button", { name: "Iniciar revisión" }).click();
  await expect(page.getByText(/Estado: COMPLETED/)).toBeVisible({ timeout: 5000 });
  await expect(page.getByText("¿Te ha ayudado esta respuesta?")).toBeVisible();
  await page.getByRole("button", { name: "No del todo" }).click();
  await page.locator("#agent-feedback-reason").selectOption("NO_CLEAR_NEXT_STEP");
  await page.locator("#agent-feedback-comment").fill("Necesito un paso siguiente más claro.");
  await page.getByRole("button", { name: "Enviar valoración" }).click();
  await expect(page.getByText("Gracias por valorar esta respuesta")).toBeVisible();
  await expect(page.getByText(/Sin siguiente paso claro/)).toBeVisible();
  const stored = await page.evaluate(() => sessionStorage.getItem("peti.lab.demo.feedback.demo-response-demo-luna"));
  expect(stored).toContain("NO_CLEAR_NEXT_STEP");
});

test("Live Runs filters are shareable in the URL and survive back navigation", async ({ page }) => {
  await page.goto("/?demo=1#ADMIN/RUNS");
  await page.getByRole("button", { name: "Safety", exact: true }).click();
  await expect(page).toHaveURL(/#ADMIN\/RUNS\?filter=SAFETY&page=1$/);
  await expect(page.getByText("demo-run-max", { exact: true })).toBeVisible();
  await expect(page.getByText("demo-run-luna", { exact: true })).not.toBeVisible();
  await page.getByText("demo-run-max", { exact: true }).click();
  await expect(page).toHaveURL(/#ADMIN\/RUNS\/demo-run-max$/);
  await page.goBack();
  await expect(page.getByRole("button", { name: "Safety", exact: true })).toHaveAttribute("aria-pressed", "true");
});
