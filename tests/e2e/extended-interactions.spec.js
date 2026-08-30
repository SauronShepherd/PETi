import { test, expect } from "@playwright/test";

test("assistant validates empty questions without leaking internals", async ({ page }) => {
  await page.goto("/?demo=1#ASSISTANT");
  await expect.poll(() => page.evaluate(() => Boolean(window.PETI_STATE?.route === "ASSISTANT" && document.querySelector("#assistant-form")))).toBe(true);
  await page.locator("#assistant-form button").click();
  await expect(page.locator("#assistant-status")).toContainText("Escribe una pregunta");
  await expect(page.locator("body")).not.toContainText("TypeError");
  await page.screenshot({ path: test.info().outputPath("assistant-empty-validation.png"), fullPage: true });
});

test("login configuration failures are rendered as plain user-safe text", async ({ page }) => {
  await page.route("**/config.example.js*", async (route) => {
    await route.fulfill({
      contentType: "application/javascript",
      body: "window.PETI_CONFIG = { apiBaseUrl: '', firebaseConfig: {} };",
    });
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Continuar con Google" }).click();
  await expect(page.locator("#auth-error")).toHaveText("Configura Firebase Web Auth para habilitar Google.");
  await expect(page.locator("#auth-error")).not.toContainText("<div");
  await expect(page.locator("body")).not.toContainText("TypeError");
  await expect(page.locator("body")).not.toContainText("FirebaseError");
});

test("Google login exposes progress and recovers after provider failure", async ({ page }) => {
  await page.goto("/");
  await expect.poll(() => page.evaluate(() => Boolean(window.PETI_STATE))).toBe(true);
  await page.evaluate(() => {
    window.PETI_STATE.firebase = {
      GoogleAuthProvider: function GoogleAuthProvider() {},
      signInWithPopup: async () => { throw { code: "auth/operation-not-allowed" }; },
    };
  });
  const button = page.getByRole("button", { name: "Continuar con Google" });
  await button.click();
  await expect(page.locator("#auth-error")).toHaveText("No se pudo iniciar sesión con Google: El acceso con Google aún no está habilitado en este entorno.");
  await expect(button).toBeEnabled();
  await expect(button).toHaveText("Continuar con Google");
  await expect(page.locator("#auth-error")).toHaveAttribute("role", "status");
  await expect(page.locator("body")).not.toContainText("FirebaseError");
});

test("documents route sends upload action to the real evidence flow", async ({ page }) => {
  await page.goto("/?demo=1#RECORDS");
  await page.getByRole("button", { name: "Subir documento" }).click();
  await expect(page.locator(".title")).toContainText("Analizar y entender");
  await expect(page.locator("#file-picker")).toBeAttached();
});

test("demo agent preview completes without calling the authenticated backend", async ({ page }) => {
  let agentRequests = 0;
  await page.route("**/v1/agent/runs**", async (route) => {
    agentRequests += 1;
    await route.abort();
  });
  await page.goto("/?demo=1&lang=en#AGENTS");
  await expect(page.locator(".demo-run-note")).toContainText("does not create a backend run");
  await page.getByRole("button", { name: "Start review" }).click();
  await expect(page.locator(".agent-stage.running .badge")).toHaveText("ORCHESTRATOR");
  await expect(page.locator("section.card p.meta").filter({ has: page.locator("code") })).toContainText("COMPLETED", { timeout: 5000 });
  expect(agentRequests).toBe(0);
  await expect(page.locator("body")).not.toContainText("API 401");
});

test("privacy export exposes a user-safe state", async ({ page }) => {
  await page.goto("/?demo=1#PROFILE");
  await page.getByRole("button", { name: "Exportar mis datos" }).click();
  await expect(page.locator("#profile-status")).toHaveText("La exportación estará disponible al iniciar sesión.");
  await expect(page.locator("body")).not.toContainText("TypeError");
  await expect(page.locator("body")).not.toContainText("API ");
});

test("care creation validates missing pet without leaking internals", async ({ page }) => {
  await page.goto("/?demo=1#CARE");
  await page.evaluate(() => { window.PETI_STATE.selectedPet = null; window.PETI_RENDER(); });
  await page.locator("#care-title").fill("Paseo de la tarde");
  await page.locator("#care-due").fill("2026-08-30T18:00");
  await page.locator("#care-form button[type=submit]").click();
  await expect(page.locator("#care-status")).toHaveText("Añade una mascota antes de crear un cuidado.");
  await expect(page.locator("body")).not.toContainText("TypeError");
});

test("care Body Check opens and preserves observable-only safety copy", async ({ page }) => {
  await page.goto("/?demo=1#CARE");
  await page.getByRole("button", { name: "Iniciar Body Check" }).click();
  await expect(page.locator(".title")).toContainText("Revisión visible de bienestar");
  await expect(page.locator("body")).toContainText("no diagnostica");
  await page.getByRole("button", { name: "Finalizar revisión" }).click();
  await expect(page.locator("#body-check-status")).toContainText("incompleta");
  await page.locator("[data-body-check]").evaluateAll((boxes) => boxes.forEach((box) => { box.checked = true; }));
  await page.getByRole("button", { name: "Finalizar revisión" }).click();
  await expect(page.locator("#body-check-status")).toContainText("inicia sesión para guardarla");
  await expect(page.locator("body")).not.toContainText("TypeError");
});

test("authenticated Body Check persists an owner-reported care record", async ({ page }) => {
  await page.goto("/?demo=1#BODY_CHECK");
  await page.evaluate(() => {
    window.PETI_STATE.selectedPet = { id: "pet-1" };
    window.PETI_STATE.user = { getIdToken: async () => "token" };
    window.__bodyCheckCall = null;
    window.PETI_API = async (path, options) => { window.__bodyCheckCall = { path, options }; return { id: "record-1" }; };
  });
  await page.locator("[data-body-check]").evaluateAll((boxes) => boxes.forEach((box) => { box.checked = true; }));
  await page.getByRole("button", { name: "Finalizar revisión" }).click();
  await expect(page.locator("#body-check-status")).toContainText("guardada en el historial");
  const call = await page.evaluate(() => window.__bodyCheckCall);
  expect(call.path).toBe("/v1/pets/pet-1/care-records");
  expect(JSON.parse(call.options.body).record_type).toBe("BODY_CHECK_MANUAL");
  expect(JSON.parse(call.options.body).source).toBe("OWNER_ENTERED");
});

test("records route renders an honest empty state", async ({ page }) => {
  await page.goto("/?demo=1#RECORDS");
  await expect(page.locator(".title")).toContainText("Documentos y registros");
  await expect(page.locator(".empty")).toContainText("No hay documentos todavía");
  await expect(page.locator("body")).not.toContainText("TypeError");
});

test("account deletion is disabled safely in demo mode", async ({ page }) => {
  await page.goto("/?demo=1#PROFILE");
  await page.getByRole("button", { name: "Eliminar cuenta" }).click();
  await expect(page.locator("#profile-status")).toHaveText("La eliminación de cuenta no está disponible en modo demo.");
  await expect(page.locator("body")).not.toContainText("API ");
});

test("settings persist language and theme locally", async ({ page }) => {
  await page.goto("/?demo=1#SETTINGS");
  await page.locator("#language-setting").selectOption("en");
  await page.locator("#theme-setting").selectOption("dark");
  await page.locator("#save-settings").click();
  await expect(page.locator("#settings-status")).toHaveText("Preferencias guardadas en este dispositivo.");
  expect(await page.evaluate(() => [localStorage.getItem("peti.language"), localStorage.getItem("peti.theme")])).toEqual(["en", "dark"]);
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect.poll(() => page.evaluate(() => getComputedStyle(document.body).backgroundColor)).not.toBe("rgb(255, 251, 247)");
});

test("plan view fails closed without exposing billing internals", async ({ page }) => {
  await page.goto("/?demo=1#PLANS");
  await expect(page.locator(".title")).toContainText("Tu plan y tus límites");
  await expect(page.locator(".notice")).toContainText("resultados existentes");
  await expect(page.locator("body")).not.toContainText("Traceback");
  await expect(page.locator("body")).not.toContainText("TypeError");
});

test("feedback requires an authenticated session without leaking internals", async ({ page }) => {
  await page.goto("/?demo=1#FEEDBACK");
  await page.locator("#feedback-message").fill("La vista es clara");
  await page.getByRole("button", { name: "Enviar feedback" }).click();
  await expect(page.locator("#feedback-status")).toHaveText("El feedback se enviará al iniciar sesión.");
  await expect(page.locator("body")).not.toContainText("TypeError");
});

test("collaboration validates missing pet safely", async ({ page }) => {
  await page.goto("/?demo=1#COLLABORATION");
  await page.evaluate(() => { window.PETI_STATE.selectedPet = null; window.PETI_RENDER(); });
  await page.locator("#member-user").fill("caregiver@example.test");
  await page.getByRole("button", { name: "Enviar invitación" }).click();
  await expect(page.locator("#collaboration-status")).toHaveText("Añade una mascota antes de compartirla.");
  await expect(page.locator("body")).not.toContainText("TypeError");
});

test("library fails closed before authentication", async ({ page }) => {
  await page.goto("/?demo=1#LIBRARY");
  await page.locator("#library-query").fill("vacuna");
  await page.getByRole("button", { name: "Buscar en mis fuentes" }).click();
  await expect(page.locator("#library-status")).toHaveText("La biblioteca se consultará al iniciar sesión.");
  await expect(page.locator("body")).not.toContainText("TypeError");
});

test("admin view fails closed for demo users", async ({ page }) => {
  await page.goto("/?demo=1#ADMIN");
  await expect(page.locator("#admin-status")).toContainText("Acceso restringido");
  await expect(page.locator("body")).not.toContainText("Traceback");
  await expect(page.locator("body")).not.toContainText("TypeError");
});
