# PETi hourly QA — 2026-08-30 22:37

## Resultado

- Suite web local inicial: 149/153 passed; 4 failed.
- Suite web local tras corregir el arnés: **153/153 passed** en desktop, tablet y móvil (4.1 min).
- Backend: `python -m pytest -q` — 446 passed, 2 warnings.
- Lint: `python -m ruff check backend` — passed.
- Producción: portada demo, JavaScript principal, imágenes de Luna y Max y API `/health/ready` — HTTP 200.
- Playwright contra producción: limitada por `ERR_NETWORK_ACCESS_DENIED` en este entorno; no se considera regresión.

## Hallazgos reproducibles

### Resuelto — condición de carrera al abrir Assistant

La prueba intentaba pulsar el formulario antes de que el arranque asíncrono hubiera aplicado la ruta `ASSISTANT`. Se añadió una espera semántica a `window.PETI_STATE.route === "ASSISTANT"` y a la presencia de `#assistant-form`. La prueba pasa en los tres tamaños de pantalla.

### Resuelto — mock de configuración Firebase no interceptaba la URL versionada

El patrón `**/config.example.js` no coincidía con `config.example.js?v=20260830`, por lo que se cargaba la configuración real. Se amplió a `**/config.example.js*`. El estado seguro esperado pasa en desktop, tablet y móvil y sigue sin filtrar `TypeError` ni `FirebaseError`.

## Evidencia positiva

Las 153 pruebas cubren rutas públicas, comparación visual con baselines en desktop/tablet/móvil, i18n, Luna y Max con cinco evidencias cada uno, flujo demo multiagente, interacciones y estados seguros. Los recursos de mascota y hojas/scripts respondieron 200 durante la suite local. No se regeneraron baselines.

## Cambios y despliegue

Se corrigieron dos defectos deterministas del arnés E2E en `tests/e2e/extended-interactions.spec.js`. No cambió ningún archivo servido ni el backend, por lo que no se realizó un despliegue redundante. La versión pública vigente se validó directamente después de la suite.

## Omisiones / riesgos

La navegación interactiva de Playwright contra producción, su consola y un pixel-diff remoto siguen limitados por `ERR_NETWORK_ACCESS_DENIED` en este entorno. Esto no afecta a la suite visual completa ejecutada localmente contra los mismos archivos servidos. Las comprobaciones HTTP públicas independientes devolvieron 200 para:

- `https://peti-care.web.app/?demo=1` (639 bytes)
- `app.js?v=20260830` (31 496 bytes)
- `assets/pets/luna-healthy-01.jpg` (43 633 bytes)
- `assets/pets/max-unhealthy-01.jpg` (44 684 bytes)
- `https://peti-api-dev-g2vgrtwnqq-ew.a.run.app/health/ready` (69 bytes)

No quedan fallos reproducibles, diferencias visuales ni anomalías de producto detectadas en este ciclo.
