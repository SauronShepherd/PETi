# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: visual-regression.spec.js >> visual baseline HOME
- Location: tests\e2e\visual-regression.spec.js:8:7

# Error details

```
Error: expect(page).toHaveScreenshot(expected) failed

  Expected an image 390px by 1840px, received 390px by 1779px. 66788 pixels (ratio 0.10 of all image pixels) are different.

  Snapshot: home.png

Call log:
  - Expect "toHaveScreenshot(home.png)" with timeout 5000ms
    - verifying given screenshot expectation
  - taking page screenshot
    - disabled all CSS animations
  - waiting for fonts to load...
  - fonts loaded
  - Expected an image 390px by 1840px, received 390px by 1779px. 66788 pixels (ratio 0.10 of all image pixels) are different.
  - waiting 100ms before taking screenshot
  - taking page screenshot
    - disabled all CSS animations
  - waiting for fonts to load...
  - fonts loaded
  - captured a stable screenshot
  - Expected an image 390px by 1840px, received 390px by 1779px. 66788 pixels (ratio 0.10 of all image pixels) are different.

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - banner [ref=e4]:
    - generic [ref=e5]:
      - generic [ref=e6]: ✤
      - text: PETi
    - generic [ref=e7]: G
  - main [ref=e10]:
    - generic [ref=e11]:
      - generic [ref=e12]:
        - generic [ref=e13]:
          - strong [ref=e14]: Demo PETi
          - generic [ref=e15]: Selecciona una mascota para probar sus evidencias.
        - generic [ref=e16]: 2 mascotas
      - generic [ref=e17]:
        - button "Luna Luna Golden retriever · Sana" [ref=e18] [cursor=pointer]:
          - img "Luna" [ref=e19]
          - generic [ref=e20]:
            - text: Luna
            - generic [ref=e21]: Golden retriever · Sana
        - button "Max Max Border collie · Observación" [ref=e22] [cursor=pointer]:
          - img "Max" [ref=e23]
          - generic [ref=e24]:
            - text: Max
            - generic [ref=e25]: Border collie · Observación
      - generic [ref=e26]:
        - generic [ref=e27]: "Evidencias de Luna:"
        - button [ref=e28] [cursor=pointer]:
          - img "Evidencia 1 de Luna" [ref=e29]
        - button [ref=e30] [cursor=pointer]:
          - img "Evidencia 2 de Luna" [ref=e31]
        - button [ref=e32] [cursor=pointer]:
          - img "Evidencia 3 de Luna" [ref=e33]
        - button [ref=e34] [cursor=pointer]:
          - img "Evidencia 4 de Luna" [ref=e35]
        - button [ref=e36] [cursor=pointer]:
          - img "Evidencia 5 de Luna" [ref=e37]
    - generic [ref=e38]: Resumen diario
    - heading "Todo lo importante, hoy." [level=1] [ref=e39]
    - paragraph [ref=e40]: Información clara para cuidar mejor a tu mascota.
    - generic [ref=e41]:
      - generic [ref=e42]:
        - generic [ref=e43]: ✤
        - generic [ref=e44]:
          - heading "Luna" [level=2] [ref=e45]
          - generic [ref=e46]: DOG · Perfil registrado
        - generic [ref=e47]: Activo
      - generic [ref=e48]:
        - text: ♡
        - strong [ref=e49]: Sin datos
        - generic [ref=e50]: Salud general
      - generic [ref=e51]:
        - text: ◌
        - strong [ref=e52]: Sin datos
        - generic [ref=e53]: Actividad
      - generic [ref=e54]:
        - text: ◉
        - strong [ref=e55]: Sin datos
        - generic [ref=e56]: Cuidados
      - generic [ref=e57]:
        - heading "Mejor siguiente paso" [level=2] [ref=e58]
        - paragraph [ref=e59]: Registra una observación o analiza una evidencia para construir un resumen basado en datos reales.
        - generic [ref=e60]:
          - button "Analizar ahora" [ref=e61] [cursor=pointer]
          - button "Ver historial" [ref=e62] [cursor=pointer]
      - generic [ref=e63]:
        - heading "Estado" [level=2] [ref=e64]
        - generic [ref=e65]:
          - strong [ref=e66]: Información honesta
          - text: Las métricas aparecen cuando existen observaciones guardadas.
  - navigation [ref=e67]:
    - button "⌂Inicio" [ref=e68] [cursor=pointer]
    - button "✦Analizar" [ref=e69] [cursor=pointer]
    - button "◷Historial" [ref=e70] [cursor=pointer]
    - button "♙Perfil" [ref=e71] [cursor=pointer]
```

# Test source

```ts
  1  | import { test, expect } from "@playwright/test";
  2  | import path from "node:path";
  3  | 
  4  | const routes = ["HOME", "SCAN", "HISTORY", "PROFILE", "AGENTS", "CARE", "BODY_CHECK", "RECORDS", "ASSISTANT", "PLANS", "SETTINGS", "FEEDBACK", "COLLABORATION", "LIBRARY", "ADMIN"];
  5  | const fixture = path.resolve(process.cwd(), "tests/fixtures/golden-retriever.jpg");
  6  | 
  7  | for (const route of routes) {
  8  |   test(`visual baseline ${route}`, async ({ page }) => {
  9  |     await page.goto(`/?demo=1#${route}`);
  10 |     await expect(page.locator("#app")).toBeVisible();
> 11 |     await expect(page).toHaveScreenshot(`${route.toLowerCase()}.png`, {
     |                        ^ Error: expect(page).toHaveScreenshot(expected) failed
  12 |       fullPage: true,
  13 |       animations: "disabled",
  14 |       caret: "hide",
  15 |       scale: "css",
  16 |       maxDiffPixelRatio: 0.01,
  17 |     });
  18 |   });
  19 | }
  20 | 
  21 | test("golden retriever fixture loads and is accepted by the demo image flow", async ({ page }) => {
  22 |   await page.goto("/?demo=1#SCAN");
  23 |   const picker = page.locator("#file-picker");
  24 |   await page.getByRole("button", { name: /Foto/ }).click();
  25 |   await picker.setInputFiles(fixture);
  26 |   await expect(page.locator("#scan-status")).toContainText("golden-retriever.jpg");
  27 |   const image = await page.evaluate(async () => {
  28 |     const response = await fetch("/assets/login-comic-background.png");
  29 |     const blob = await response.blob();
  30 |     return { type: blob.type, size: blob.size };
  31 |   });
  32 |   expect(image.type).toMatch(/^image\//);
  33 |   expect(image.size).toBeGreaterThan(1000);
  34 | });
  35 | 
  36 | test("demo exercises two synthetic pets with five observations each", async ({ page }) => {
  37 |   await page.goto("/?demo=1#SCAN");
  38 |   const picker = page.locator("#file-picker");
  39 |   const pets = [
  40 |     { id: "demo-luna", name: "Luna", files: ["luna-healthy-01.jpg", "luna-healthy-02.jpg", "luna-healthy-03.jpg", "luna-healthy-04.jpg", "luna-healthy-05.jpg"] },
  41 |     { id: "demo-max", name: "Max", files: ["max-unhealthy-01.jpg", "max-unhealthy-02.jpg", "max-unhealthy-03.jpg", "max-unhealthy-04.jpg", "max-unhealthy-05.jpg"] },
  42 |   ];
  43 |   for (const pet of pets) {
  44 |     await page.evaluate((value) => { window.PETI_STATE.selectedPet = value; }, { id: pet.id, display_name: pet.name, species: "DOG" });
  45 |     for (const file of pet.files) {
  46 |       await picker.setInputFiles(path.resolve(process.cwd(), "tests/fixtures/dogs", file));
  47 |       await expect(page.locator("#scan-status")).toContainText(file);
  48 |     }
  49 |   }
  50 | });
  51 | 
```