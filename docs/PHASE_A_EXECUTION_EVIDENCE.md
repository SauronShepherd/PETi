# Fase A — evidencia de ejecución

Fecha de ejecución: 2026-08-29

## Alcance congelado

El escenario principal del MVP es **PETi Check** para un perro: el dueño registra
un objetivo y evidencia multimodal; el backend ejecuta el workflow multiagente y
devuelve observaciones acotadas, incertidumbres, provenance y estado de seguridad.
Los especialistas adicionales son extensiones y no son necesarios para este
camino principal.

## Cambios implementados

- La API devuelve `profile_complete` explícitamente.
- Una mascota creada solo con nombre y especie devuelve `profile_complete: false`.
- La API no inventa `health_score`, `weight` ni `activity` al crear una mascota.
- El cliente Android conserva `profile_complete` al parsear la respuesta.
- La interfaz muestra `Completar perfil` y oculta métricas/recordatorios hasta
  que existan datos suficientes.
- La arquitectura de ejecución usa Google ADK y mantiene la separación Android →
  API → agentes → worker → Firestore.
- Android Gradle Plugin actualizado a `8.13.2` para corregir el fallo interno de
  Lint/UAST que impedía validar la instalación local.

## Comandos y resultados

| Comprobación | Resultado |
|---|---|
| `python -m pytest backend/tests -q` | **484 passed** |
| `python -m ruff check backend/app backend/tests` | **All checks passed** |
| `scripts/check.ps1` | **All checks passed** |
| `:app:assembleDebug` | **BUILD SUCCESSFUL** |
| `:app:testDebugUnitTest` | **BUILD SUCCESSFUL** |
| `:app:lintDebug` | **BUILD SUCCESSFUL** |
| `:features:funding:lintDebug` | **BUILD SUCCESSFUL** |
| `:app:connectedDebugAndroidTest` | **10 tests, 0 failed** en `PETi_Phase0_API35_clean` |

## Criterio de salida

La implementación, el análisis estático y las pruebas funcionales de Fase A están
completas y verificadas localmente.
