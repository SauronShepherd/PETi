# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: extended-interactions.spec.js >> assistant validates empty questions without leaking internals
- Location: tests\e2e\extended-interactions.spec.js:3:5

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.goto: net::ERR_ABORTED; maybe frame was detached?
Call log:
  - navigating to "https://peti-care.web.app/?demo=1#ASSISTANT", waiting until "load"

```

# Test source

```ts
  1   | import { test, expect } from "@playwright/test";
  2   | 
  3   | test("assistant validates empty questions without leaking internals", async ({ page }) => {
> 4   |   await page.goto("/?demo=1#ASSISTANT");
      |              ^ Error: page.goto: net::ERR_ABORTED; maybe frame was detached?
  5   |   await page.locator("#assistant-form button").click();
  6   |   await expect(page.locator("#assistant-status")).toContainText("Escribe una pregunta");
  7   |   await expect(page.locator("body")).not.toContainText("TypeError");
  8   |   await page.screenshot({ path: test.info().outputPath("assistant-empty-validation.png"), fullPage: true });
  9   | });
  10  | 
  11  | test("login configuration failures are rendered as plain user-safe text", async ({ page }) => {
  12  |   await page.route("**/config.example.js", async (route) => {
  13  |     await route.fulfill({
  14  |       contentType: "application/javascript",
  15  |       body: "window.PETI_CONFIG = { apiBaseUrl: '', firebaseConfig: {} };",
  16  |     });
  17  |   });
  18  |   await page.goto("/");
  19  |   await page.getByRole("button", { name: "Continuar con Google" }).click();
  20  |   await expect(page.locator("#auth-error")).toHaveText("Configura Firebase Web Auth para habilitar Google.");
  21  |   await expect(page.locator("#auth-error")).not.toContainText("<div");
  22  |   await expect(page.locator("body")).not.toContainText("TypeError");
  23  |   await expect(page.locator("body")).not.toContainText("FirebaseError");
  24  | });
  25  | 
  26  | test("Google login exposes progress and recovers after provider failure", async ({ page }) => {
  27  |   await page.goto("/");
  28  |   await expect.poll(() => page.evaluate(() => Boolean(window.PETI_STATE))).toBe(true);
  29  |   await page.evaluate(() => {
  30  |     window.PETI_STATE.firebase = {
  31  |       GoogleAuthProvider: function GoogleAuthProvider() {},
  32  |       signInWithPopup: async () => { throw { code: "auth/operation-not-allowed" }; },
  33  |     };
  34  |   });
  35  |   const button = page.getByRole("button", { name: "Continuar con Google" });
  36  |   await button.click();
  37  |   await expect(page.locator("#auth-error")).toHaveText("No se pudo iniciar sesión con Google: El acceso con Google aún no está habilitado en este entorno.");
  38  |   await expect(button).toBeEnabled();
  39  |   await expect(button).toHaveText("Continuar con Google");
  40  |   await expect(page.locator("#auth-error")).toHaveAttribute("role", "status");
  41  |   await expect(page.locator("body")).not.toContainText("FirebaseError");
  42  | });
  43  | 
  44  | test("documents route sends upload action to the real evidence flow", async ({ page }) => {
  45  |   await page.goto("/?demo=1#RECORDS");
  46  |   await page.getByRole("button", { name: "Subir documento" }).click();
  47  |   await expect(page.locator(".title")).toContainText("Analizar y entender");
  48  |   await expect(page.locator("#file-picker")).toBeAttached();
  49  | });
  50  | 
  51  | test("privacy export exposes a user-safe state", async ({ page }) => {
  52  |   await page.goto("/?demo=1#PROFILE");
  53  |   await page.getByRole("button", { name: "Exportar mis datos" }).click();
  54  |   await expect(page.locator("#profile-status")).toHaveText("La exportación estará disponible al iniciar sesión.");
  55  |   await expect(page.locator("body")).not.toContainText("TypeError");
  56  |   await expect(page.locator("body")).not.toContainText("API ");
  57  | });
  58  | 
  59  | test("care creation validates missing pet without leaking internals", async ({ page }) => {
  60  |   await page.goto("/?demo=1#CARE");
  61  |   await page.evaluate(() => { window.PETI_STATE.selectedPet = null; window.PETI_RENDER(); });
  62  |   await page.locator("#care-title").fill("Paseo de la tarde");
  63  |   await page.locator("#care-due").fill("2026-08-30T18:00");
  64  |   await page.locator("#care-form button[type=submit]").click();
  65  |   await expect(page.locator("#care-status")).toHaveText("Añade una mascota antes de crear un cuidado.");
  66  |   await expect(page.locator("body")).not.toContainText("TypeError");
  67  | });
  68  | 
  69  | test("care Body Check opens and preserves observable-only safety copy", async ({ page }) => {
  70  |   await page.goto("/?demo=1#CARE");
  71  |   await page.getByRole("button", { name: "Iniciar Body Check" }).click();
  72  |   await expect(page.locator(".title")).toContainText("Revisión visible de bienestar");
  73  |   await expect(page.locator("body")).toContainText("no diagnostica");
  74  |   await page.getByRole("button", { name: "Finalizar revisión" }).click();
  75  |   await expect(page.locator("#body-check-status")).toContainText("incompleta");
  76  |   await page.locator("[data-body-check]").evaluateAll((boxes) => boxes.forEach((box) => { box.checked = true; }));
  77  |   await page.getByRole("button", { name: "Finalizar revisión" }).click();
  78  |   await expect(page.locator("#body-check-status")).toContainText("inicia sesión para guardarla");
  79  |   await expect(page.locator("body")).not.toContainText("TypeError");
  80  | });
  81  | 
  82  | test("authenticated Body Check persists an owner-reported care record", async ({ page }) => {
  83  |   await page.goto("/?demo=1#BODY_CHECK");
  84  |   await page.evaluate(() => {
  85  |     window.PETI_STATE.selectedPet = { id: "pet-1" };
  86  |     window.PETI_STATE.user = { getIdToken: async () => "token" };
  87  |     window.__bodyCheckCall = null;
  88  |     window.PETI_API = async (path, options) => { window.__bodyCheckCall = { path, options }; return { id: "record-1" }; };
  89  |   });
  90  |   await page.locator("[data-body-check]").evaluateAll((boxes) => boxes.forEach((box) => { box.checked = true; }));
  91  |   await page.getByRole("button", { name: "Finalizar revisión" }).click();
  92  |   await expect(page.locator("#body-check-status")).toContainText("guardada en el historial");
  93  |   const call = await page.evaluate(() => window.__bodyCheckCall);
  94  |   expect(call.path).toBe("/v1/pets/pet-1/care-records");
  95  |   expect(JSON.parse(call.options.body).record_type).toBe("BODY_CHECK_MANUAL");
  96  |   expect(JSON.parse(call.options.body).source).toBe("OWNER_ENTERED");
  97  | });
  98  | 
  99  | test("records route renders an honest empty state", async ({ page }) => {
  100 |   await page.goto("/?demo=1#RECORDS");
  101 |   await expect(page.locator(".title")).toContainText("Documentos y registros");
  102 |   await expect(page.locator(".empty")).toContainText("No hay documentos todavía");
  103 |   await expect(page.locator("body")).not.toContainText("TypeError");
  104 | });
```