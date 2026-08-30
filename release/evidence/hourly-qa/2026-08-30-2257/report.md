# PETi hourly QA — 2026-08-30 22:57

## Resultado

- Navegación interactiva contra `https://peti-care.web.app/?demo=1`: completada en escritorio y móvil.
- Consola del navegador: sin errores ni advertencias.
- Integridad visual: sin imágenes rotas, IDs duplicados ni desbordamiento horizontal.
- Flujo multiagente demo: recorrido completo hasta `COMPLETED`, sin llamada al backend autenticado.
- Suite E2E y visual final: **156/156 passed** en desktop, tablet y móvil (3.7 min).

## Hallazgo y corrección

### P1 visual — las evidencias 3–5 de Max mostraban otra mascota

Al seleccionar a Max en la web pública, las dos primeras evidencias eran del border collie, pero las tres restantes mostraban un golden retriever. El código apuntaba a los nombres correctos; el contenido binario de `max-unhealthy-03.jpg`, `04.jpg` y `05.jpg` estaba mal asignado.

Se generaron tres fotografías nuevas, realistas y no gráficas, conservando la identidad de Max: border collie adulto blanco y negro, un ojo marrón y otro azul claro, mismo patrón facial y postura de baja energía que requiere observación. Se sustituyeron tanto los recursos web como sus fixtures de prueba.

La primera comprobación post-deploy confirmó que Firebase contenía los binarios correctos, pero un navegador previamente abierto aún mostraba las imágenes antiguas por caché. Los tres nombres se versionaron con `-v2` y se añadió `Cache-Control: no-cache, max-age=0, must-revalidate` a `/assets/pets/**` para evitar futuras sustituciones invisibles.

## Protección contra regresiones

- Se añadió una baseline visual dedicada al panel de evidencias de Max.
- La baseline se revisó en desktop, tablet y móvil.
- La suite pasa ahora de 153 a 156 pruebas.
- Se eliminó una condición de carrera del test del flujo multiagente: valida la creación del run y su llegada a `COMPLETED` sin depender de capturar un estado de 500 ms.

## Evidencia visual revisada

Las cinco miniaturas de Max corresponden ahora al mismo border collie. En móvil el panel reorganiza las evidencias en dos filas, mantiene objetivos táctiles suficientes y no produce scroll horizontal.

## Despliegue y validación pública

Pendiente de completar en este ciclo.
