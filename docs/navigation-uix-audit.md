# Auditoría automática de navegación y UIX

Fecha: 2026-08-28  
Aplicación: PETi Android  
Referencias: `C:\ANGEL\Personal\Hackathons\20260817 - Gemini - PETI\UIX`

## Alcance

Se ha utilizado un AVD API 35 y navegación automatizada mediante `adb`, además de los tests instrumentados Compose existentes. Las acciones ejecutadas fueron:

1. Lanzamiento limpio de `MainActivity`.
2. Captura de la pantalla de acceso.
3. Autenticación local de debug.
4. Creación de una mascota de prueba.
5. Acceso a Home.
6. Navegación a Analizar.
7. Navegación a Historial.
8. Navegación a Perfil.
9. Ejecución automática de la suite instrumentada completa.

Evidencias generadas:

- `C:\Temp\peti-audit-01-signedout.png`
- `C:\Temp\peti-audit-02-authenticated.png`
- `C:\Temp\peti-audit-03-home.png`
- `C:\Temp\peti-audit-04-scan.png`
- `C:\Temp\peti-audit-05-history.png`
- `C:\Temp\peti-audit-06-profile.png`
- `C:\Temp\peti-audit-relaunch-2.png`

## Resultado funcional

### Validado

- La aplicación arranca mediante lanzamiento explícito de `MainActivity`.
- La pantalla de acceso muestra el CTA `Continuar con Google`.
- La autenticación local de debug funciona.
- Se puede crear una mascota.
- La mascota queda seleccionada como activa.
- Home muestra el dashboard cuando existe una mascota.
- La navegación inferior cambia de sección.
- La pantalla Analizar muestra las opciones de análisis.
- Los tests instrumentados validan los contratos principales.

### Resultados automáticos

- Backend: 481 tests pasando.
- Android unitario: pasando.
- Android instrumentado: 9/9 pasando.
- Compilación debug: pasando.
- Compilación release: pasando.

## Incidencias detectadas

### P0 — Arranque no completamente reproducible bajo lanzamiento genérico

**Evidencia:** durante un arranque con `monkey` el AVD mostró un ANR y posteriormente quedó enfocada una aplicación externa (`Messaging`). El lanzamiento explícito posterior de `com.peti.app.debug/.MainActivity` funcionó.

**Diagnóstico actual:** el resultado mezcla estado contaminado del AVD, actividad externa y una ejecución de arranque que no permite atribuir definitivamente el ANR a PETi. No se considera cerrado hasta reproducir 20 arranques limpios con la actividad explícita y sin ANR.

**Solución:** añadir un smoke test de arranque explícito que:

- detenga el proceso;
- lance `MainActivity` por componente;
- espere la ventana de PETi;
- compruebe ausencia de ANR/crash;
- capture screenshot;
- repita el ciclo varias veces.

### P1 — La pantalla de acceso no reproduce el onboarding UIX

**Evidencia:** `peti-audit-relaunch-2.png` muestra una tarjeta funcional, pero no la composición de referencia con ilustración/fotografía, logo completo, decoración crema, copy de bienvenida y composición editorial.

**Solución:** implementar `WelcomeScreen` con:

- logo vectorial PETi;
- imagen de mascota;
- fondo crema decorativo;
- bloque de bienvenida;
- CTA principal teal;
- CTA secundario de correo;
- términos y privacidad;
- enlace de inicio de sesión.

### P1 — Home todavía no alcanza la densidad visual de UIX

**Evidencia:** Home ya contiene score, recordatorio y métricas, pero carece de fotografía real, gráfico de actividad, escaneos recientes y composición equivalente a las referencias.

**Solución:** completar `PetiDashboard` con componentes visuales reales:

- `PetiPetHeroCard` con imagen;
- `PetiHealthScore` circular;
- `PetiReminderCard`;
- `PetiActivityGrid`;
- `PetiRecentScanCard`;
- `PetiNextActionCard`.

### P1 — Navegación inferior visualmente sobredimensionada

**Evidencia:** la navegación ocupa una fracción excesiva de la pantalla del AVD y los textos/iconos son mayores que en las referencias UIX.

**Solución:** ajustar la barra a:

- altura fija de 72–80dp;
- iconos de 22–24dp;
- etiquetas de 11–12sp;
- estado activo mediante color teal y fondo suave;
- separación y padding coherentes con el sistema visual.

### P1 — Pantallas internas aún presentan UI técnica

**Evidencia:** Analizar, Historial y Perfil todavía dependen de paneles genéricos y campos de implementación. No tienen todavía la composición de las imágenes UIX.

**Solución:** sustituir progresivamente los paneles por pantallas específicas:

- `AnalyzeScreen`;
- `CaptureScreen`;
- `AnalysisResultScreen`;
- `HistoryScreen`;
- `CareScreen`;
- `ProfileScreen`;
- `DocumentsScreen`;
- `SettingsScreen`.

### P2 — Identificadores técnicos visibles

**Evidencia:** algunos estados y payloads pueden mostrar identificadores o nombres técnicos cuando hay errores o resultados incompletos.

**Solución:** introducir un mapper único de presentación que traduzca estados, tipos de operación y errores antes de llegar a Compose.

### P2 — Cobertura visual insuficiente

**Evidencia:** la suite actual prueba comportamiento y accesibilidad, pero no compara screenshots con las referencias UIX.

**Solución:** añadir screenshots automáticos por pantalla y por estado:

- signed out;
- onboarding vacío;
- Home con mascota;
- Home sin datos;
- Analizar;
- captura;
- resultado;
- historial vacío;
- historial con datos;
- cuidados;
- perfil;
- documentos;
- ajustes;
- errores y loading.

## Evaluación UIX

| Área | Estado |
|---|---|
| Paleta teal/coral/crema | Parcialmente alineada |
| Radios y tarjetas | Parcialmente alineados |
| Logo PETi | Insuficiente |
| Fotografías/ilustraciones | Insuficiente |
| Home/dashboard | Parcial |
| Analizar | Parcial |
| Captura/resultados | Insuficiente |
| Historial | Insuficiente |
| Cuidados/calendario | Insuficiente |
| Perfil/mediciones | Insuficiente |
| Documentos/ajustes | Insuficiente |
| Navegación inferior | Funcional, visualmente sobredimensionada |
| Localización española | Parcial |

## Plan de corrección

1. Crear el sistema visual definitivo y assets locales.
2. Extraer la navegación y cabecera como componentes reutilizables.
3. Completar Welcome/Onboarding.
4. Completar Home con los bloques exactos de UIX.
5. Completar Analizar, Captura y Resultado.
6. Completar Historial y detalle.
7. Completar Cuidados, Calendario y Body Check.
8. Completar Perfil, Mediciones y Registros.
9. Completar Documentos, revisión y Ajustes.
10. Añadir screenshots automáticos y comparación visual.
11. Repetir navegación completa en AVD limpio.
12. Ejecutar backend, unitarios, instrumentación, lint y release.

## Criterio de cierre

La auditoría se considerará cerrada únicamente cuando:

- cada pantalla UIX tenga una implementación equivalente;
- cada acción crítica tenga test automático;
- cada screenshot esperado pase la revisión visual;
- no existan textos técnicos visibles;
- no existan CTAs de monetización;
- no haya ANR/crashes en 20 arranques limpios;
- toda la suite automática y el build release pasen.

## Correcciones aplicadas después de la auditoría

- La pantalla Home fue rediseñada con tarjetas de mascota, salud, recordatorio, métricas y siguiente acción.
- La pantalla Analizar fue rediseñada con tarjetas visuales para vídeo, foto, digestivo/heces y condición corporal.
- La navegación inferior se fijó fuera del scroll y se redujo a una altura y tipografía más próximas a UIX.
- Se eliminaron etiquetas técnicas visibles en resultados y se tradujeron instrucciones restantes.
- La compilación Kotlin y los tests unitarios Android volvieron a pasar tras los cambios.
- Se realizaron 10 arranques explícitos automáticos adicionales; todos conservaron el foco en `com.peti.app.debug` y no generaron señales nuevas de ANR/crash.
- Se generaron nuevas capturas de acceso, autenticación, Home, Analizar, Historial y Perfil en `C:\Temp\peti-navigation-audit`.

## Estado pendiente tras esta iteración

- Las pantallas de bienvenida, captura, resultado, historial, cuidados, perfil, documentos y ajustes todavía necesitan la misma composición visual específica de las referencias.
- Faltan assets locales de fotografía/ilustración y comparación automática de screenshots.
- El smoke test de 20 arranques limpios sigue pendiente para cerrar definitivamente el incidente P0 de arranque.

## Hallazgos de la segunda navegación automática

- El flujo de `adb` basado en coordenadas no es estable cuando el teclado está abierto: el texto de prueba se concatenó (`AuditPetAuditPet`) y la pulsación posterior no llegó siempre al botón esperado. Esto no invalida los tests Compose, pero sí demuestra que el recorrido externo necesita selectores semánticos o un driver UI automatizado, no coordenadas fijas.
- En estado sin mascota, las cuatro secciones siguen mostrando el mismo bloque de onboarding porque la navegación permite cambiar de pestaña aunque no exista un perfil activo. Debe sustituirse por estados vacíos contextuales o bloquear las secciones dependientes de mascota con una acción clara.
- Las capturas corregidas muestran que la navegación es funcional, pero el producto todavía no alcanza las referencias UIX en fotografía, composición editorial y pantallas de contenido.

## Corrección posterior

- Las entradas de navegación Analizar, Historial y Perfil quedan deshabilitadas sin mascota activa; se evita mostrar contenido genérico fuera de contexto.
- La compilación debug, los tests unitarios y los 9 tests instrumentados vuelven a pasar tras esta corrección.

## Corrección posterior: Perfil y cuidados

- Perfil/Historial se presenta ahora como una ficha de producto: “Perfil y registros”, información segura, accesos rápidos y acciones de búsqueda/exportación diferenciadas.
- Se eliminaron los últimos mensajes visibles en inglés del flujo de línea de tiempo, mediciones y cuidados.
- Se mantienen los contratos de automatización (`historySearch`, `historyExport`, `phase6*`) para evitar regresiones funcionales.
- Verificación automática: `:app:compileDebugKotlin`, `:app:testDebugUnitTest` y `:app:connectedDebugAndroidTest` (9/9) pasan.

## Auditoría automática ampliada — 28/08/2026

### Recorrido ejecutado

Se añadió `FullNavigationEvidenceTest`, basado en Semantics de Compose y sin coordenadas fijas. El recorrido captura evidencia después de cada carga/acción relevante:

1. Acceso público.
2. Autenticación local de prueba.
3. Estado sin mascotas.
4. Formulario de alta cumplimentado.
5. Inicio con mascota.
6. Navegación a Analizar.
7. Controles de Foto, Cámara, Vídeo y Audio.
8. Navegación a Historial.
9. Línea temporal, mediciones y registros.
10. Navegación a Perfil.
11. Búsqueda/exportación del historial.

Las capturas se generan automáticamente en el directorio externo privado de la app durante el test, evitando permisos públicos y eliminando la dependencia del emulador interactivo.

### Resultado

- `connectedDebugAndroidTest`: 10/10 tests correctos.
- `compileDebugAndroidTestKotlin`: correcto.
- Se añadieron identificadores únicos `nav-HOME`, `nav-SCAN`, `nav-HISTORY` y `nav-PROFILE` para navegación semántica estable.
- Se detectó y corrigió un selector ambiguo: “Historial” existía tanto en la barra inferior como en el contenido.
- Se detectó y corrigió un problema del arnés de captura: Android 35 rechaza rutas directas bajo `/sdcard`; ahora se usa almacenamiento externo privado de la aplicación.
- El diagnóstico de bounds/viewport se certificó finalmente en móvil: 10/10 tests instrumentados pasan después de ejecutar las capturas en el hilo principal y excluir contenedores semánticos no dimensionables.

### Inventario de rutas solicitadas que no existen en la app Android actual

No se encontraron superficies públicas separadas para grupos, biblioteca, artículos, variantes, controles de administración, comentarios, feedback, idioma, tema, guardado o suscripción. No se marcan como “pasadas”: son huecos funcionales que requieren decidir e implementar una ruta antes de poder automatizarla.

### Diagnóstico UI/UX

El test actual valida presencia, interacción y navegación, pero todavía no calcula automáticamente overflow, bounds fuera de viewport, imágenes rotas, contraste ni comparación pixel/estructura contra las referencias UIX. Esos criterios quedan registrados como bloque de auditoría visual pendiente; las capturas de referencia siguen mostrando una composición editorial, fotografía de mascota y navegación por pantalla que la implementación actual aún no reproduce completamente.

Se añadió `scripts/analyze_navigation_evidence.py` y su salida `docs/navigation-uix-metrics.json`. Sobre las 16 capturas históricas disponibles, las 16 tienen resolución 1080×1920, no presentan señal de pantalla completamente vacía y el análisis deja explícitamente sin falsear el contraste, overflow e imágenes rotas cuando no existe información de bounds/semántica suficiente.

## Matriz de dispositivos

- Móvil Pixel 2/API 35: recorrido instrumentado completado, 10/10 tests.
- Tablet Pixel Tablet/API 35: configuración añadida como dispositivo gestionado (`phase0TabletApi35DebugAndroidTest`), pero la preparación del AVD quedó bloqueada en este entorno después de `phase0TabletApi35Setup`; no se contabiliza como pasada.
- Escritorio: no existe target Android/Desktop en este proyecto; no se puede afirmar cobertura de escritorio hasta crear un target Compose Desktop o una aplicación web específica.
