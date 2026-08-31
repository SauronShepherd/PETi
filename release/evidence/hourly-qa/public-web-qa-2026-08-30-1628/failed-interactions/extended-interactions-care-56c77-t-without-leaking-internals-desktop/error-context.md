# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: extended-interactions.spec.js >> care creation validates missing pet without leaking internals
- Location: tests\e2e\extended-interactions.spec.js:59:5

# Error details

```
Error: expect(locator).toHaveText(expected) failed

Locator:  locator('#care-status')
Expected: "Añade una mascota antes de crear un cuidado."
Received: "No se pudo guardar el evento. Inténtalo de nuevo."
Timeout:  5000ms

Call log:
  - Expect "toHaveText" with timeout 5000ms
  - waiting for locator('#care-status')
    5 × locator resolved to <div id="care-status" class="footer-note">Guardando evento…</div>
      - unexpected value "Guardando evento…"
    9 × locator resolved to <div id="care-status" class="footer-note">No se pudo guardar el evento. Inténtalo de nuevo.</div>
      - unexpected value "No se pudo guardar el evento. Inténtalo de nuevo."

```

```yaml
- text: No se pudo guardar el evento. Inténtalo de nuevo.
```

# Test source

```ts
  1   | import { test, expect } from "@playwright/test";
  2   | 
  3   | test("assistant validates empty questions without leaking internals", async ({ page }) => {
  4   |   await page.goto("/?demo=1#ASSISTANT");
  5   |   await page.locator("#assistant-form button").click();
  6   |   await expect(page.locator("#assistant-status")).toContainText("Añade una mascota");
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
> 64  |   await expect(page.locator("#care-status")).toHaveText("Añade una mascota antes de crear un cuidado.");
      |                                              ^ Error: expect(locator).toHaveText(expected) failed
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
  107 |   await page.getByRole("button", { name: "Eliminar cuenta" }).click();
  108 |   await expect(page.locator("#profile-status")).toHaveText("La eliminación de cuenta no está disponible en modo demo.");
  109 |   await expect(page.locator("body")).not.toContainText("API ");
  110 | });
  111 | 
  112 | test("settings persist language and theme locally", async ({ page }) => {
  113 |   await page.goto("/?demo=1#SETTINGS");
  114 |   await page.locator("#language-setting").selectOption("en");
  115 |   await page.locator("#theme-setting").selectOption("dark");
  116 |   await page.locator("#save-settings").click();
  117 |   await expect(page.locator("#settings-status")).toHaveText("Preferencias guardadas en este dispositivo.");
  118 |   expect(await page.evaluate(() => [localStorage.getItem("peti.language"), localStorage.getItem("peti.theme")])).toEqual(["en", "dark"]);
  119 |   await expect(page.locator("html")).toHaveAttribute("lang", "en");
  120 |   await expect.poll(() => page.evaluate(() => getComputedStyle(document.body).backgroundColor)).not.toBe("rgb(255, 251, 247)");
  121 | });
  122 | 
  123 | test("plan view fails closed without exposing billing internals", async ({ page }) => {
  124 |   await page.goto("/?demo=1#PLANS");
  125 |   await expect(page.locator(".title")).toContainText("Tu plan y tus límites");
  126 |   await expect(page.locator(".notice")).toContainText("resultados existentes");
  127 |   await expect(page.locator("body")).not.toContainText("Traceback");
  128 |   await expect(page.locator("body")).not.toContainText("TypeError");
  129 | });
  130 | 
  131 | test("feedback requires an authenticated session without leaking internals", async ({ page }) => {
  132 |   await page.goto("/?demo=1#FEEDBACK");
  133 |   await page.locator("#feedback-message").fill("La vista es clara");
  134 |   await page.getByRole("button", { name: "Enviar feedback" }).click();
  135 |   await expect(page.locator("#feedback-status")).toHaveText("El feedback se enviará al iniciar sesión.");
  136 |   await expect(page.locator("body")).not.toContainText("TypeError");
  137 | });
  138 | 
  139 | test("collaboration validates missing pet safely", async ({ page }) => {
  140 |   await page.goto("/?demo=1#COLLABORATION");
  141 |   await page.locator("#member-user").fill("caregiver@example.test");
  142 |   await page.getByRole("button", { name: "Enviar invitación" }).click();
  143 |   await expect(page.locator("#collaboration-status")).toHaveText("Añade una mascota antes de compartirla.");
  144 |   await expect(page.locator("body")).not.toContainText("TypeError");
  145 | });
  146 | 
  147 | test("library fails closed before authentication", async ({ page }) => {
  148 |   await page.goto("/?demo=1#LIBRARY");
  149 |   await page.locator("#library-query").fill("vacuna");
  150 |   await page.getByRole("button", { name: "Buscar en mis fuentes" }).click();
  151 |   await expect(page.locator("#library-status")).toHaveText("La biblioteca se consultará al iniciar sesión.");
  152 |   await expect(page.locator("body")).not.toContainText("TypeError");
  153 | });
  154 | 
  155 | test("admin view fails closed for demo users", async ({ page }) => {
  156 |   await page.goto("/?demo=1#ADMIN");
  157 |   await expect(page.locator("#admin-status")).toContainText("Acceso restringido");
  158 |   await expect(page.locator("body")).not.toContainText("Traceback");
  159 |   await expect(page.locator("body")).not.toContainText("TypeError");
  160 | });
  161 | 
```