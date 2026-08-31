# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: extended-interactions.spec.js >> collaboration validates missing pet safely
- Location: tests\e2e\extended-interactions.spec.js:139:5

# Error details

```
Error: expect(locator).toHaveText(expected) failed

Locator:  locator('#collaboration-status')
Expected: "Añade una mascota antes de compartirla."
Received: "La invitación se enviará al iniciar sesión."
Timeout:  5000ms

Call log:
  - Expect "toHaveText" with timeout 5000ms
  - waiting for locator('#collaboration-status')
    14 × locator resolved to <div class="footer-note" id="collaboration-status">La invitación se enviará al iniciar sesión.</div>
       - unexpected value "La invitación se enviará al iniciar sesión."

```

```yaml
- text: La invitación se enviará al iniciar sesión.
```

# Test source

```ts
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
> 143 |   await expect(page.locator("#collaboration-status")).toHaveText("Añade una mascota antes de compartirla.");
      |                                                       ^ Error: expect(locator).toHaveText(expected) failed
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