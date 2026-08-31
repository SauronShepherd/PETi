# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: extended-interactions.spec.js >> assistant validates empty questions without leaking internals
- Location: tests\e2e\extended-interactions.spec.js:3:5

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: locator('#assistant-status')
Expected substring: "Añade una mascota"
Received string:    "Escribe una pregunta."
Timeout: 5000ms

Call log:
  - Expect "toContainText" with timeout 5000ms
  - waiting for locator('#assistant-status')
    14 × locator resolved to <div class="footer-note" id="assistant-status">Escribe una pregunta.</div>
       - unexpected value "Escribe una pregunta."

```

```yaml
- text: Escribe una pregunta.
```

# Test source

```ts
  1   | import { test, expect } from "@playwright/test";
  2   | 
  3   | test("assistant validates empty questions without leaking internals", async ({ page }) => {
  4   |   await page.goto("/?demo=1#ASSISTANT");
  5   |   await page.locator("#assistant-form button").click();
> 6   |   await expect(page.locator("#assistant-status")).toContainText("Añade una mascota");
      |                                                   ^ Error: expect(locator).toContainText(expected) failed
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
  61  |   await page.locator("#care-title").fill("Paseo de la tarde");
  62  |   await page.locator("#care-due").fill("2026-08-30T18:00");
  63  |   await page.locator("#care-form button[type=submit]").click();
  64  |   await expect(page.locator("#care-status")).toHaveText("Añade una mascota antes de crear un cuidado.");
  65  |   await expect(page.locator("body")).not.toContainText("TypeError");
  66  | });
  67  | 
  68  | test("care Body Check opens and preserves observable-only safety copy", async ({ page }) => {
  69  |   await page.goto("/?demo=1#CARE");
  70  |   await page.getByRole("button", { name: "Iniciar Body Check" }).click();
  71  |   await expect(page.locator(".title")).toContainText("Revisión visible de bienestar");
  72  |   await expect(page.locator("body")).toContainText("no diagnostica");
  73  |   await page.getByRole("button", { name: "Finalizar revisión" }).click();
  74  |   await expect(page.locator("#body-check-status")).toContainText("incompleta");
  75  |   await page.locator("[data-body-check]").evaluateAll((boxes) => boxes.forEach((box) => { box.checked = true; }));
  76  |   await page.getByRole("button", { name: "Finalizar revisión" }).click();
  77  |   await expect(page.locator("#body-check-status")).toContainText("inicia sesión para guardarla");
  78  |   await expect(page.locator("body")).not.toContainText("TypeError");
  79  | });
  80  | 
  81  | test("authenticated Body Check persists an owner-reported care record", async ({ page }) => {
  82  |   await page.goto("/?demo=1#BODY_CHECK");
  83  |   await page.evaluate(() => {
  84  |     window.PETI_STATE.selectedPet = { id: "pet-1" };
  85  |     window.PETI_STATE.user = { getIdToken: async () => "token" };
  86  |     window.__bodyCheckCall = null;
  87  |     window.PETI_API = async (path, options) => { window.__bodyCheckCall = { path, options }; return { id: "record-1" }; };
  88  |   });
  89  |   await page.locator("[data-body-check]").evaluateAll((boxes) => boxes.forEach((box) => { box.checked = true; }));
  90  |   await page.getByRole("button", { name: "Finalizar revisión" }).click();
  91  |   await expect(page.locator("#body-check-status")).toContainText("guardada en el historial");
  92  |   const call = await page.evaluate(() => window.__bodyCheckCall);
  93  |   expect(call.path).toBe("/v1/pets/pet-1/care-records");
  94  |   expect(JSON.parse(call.options.body).record_type).toBe("BODY_CHECK_MANUAL");
  95  |   expect(JSON.parse(call.options.body).source).toBe("OWNER_ENTERED");
  96  | });
  97  | 
  98  | test("records route renders an honest empty state", async ({ page }) => {
  99  |   await page.goto("/?demo=1#RECORDS");
  100 |   await expect(page.locator(".title")).toContainText("Documentos y registros");
  101 |   await expect(page.locator(".empty")).toContainText("No hay documentos todavía");
  102 |   await expect(page.locator("body")).not.toContainText("TypeError");
  103 | });
  104 | 
  105 | test("account deletion is disabled safely in demo mode", async ({ page }) => {
  106 |   await page.goto("/?demo=1#PROFILE");
```