# PETi — Plan exhaustivo para una aplicación multiagente operativa

Estado: plan de ejecución. Una casilla solo se marca cuando existe implementación y evidencia verificable.

## 0. Objetivo y restricciones

Objetivo: entregar una app Android para dueños de perros donde un objetivo se convierta en un workflow multiagente, asíncrono, durable, seguro y útil.

Restricciones:

- No añadir ni modificar CI.
- No desplegar producción.
- No guardar ni mostrar secretos, tokens, contraseñas o API keys.
- No permitir que un modelo cambie ownership, permisos, estado durable o guardrails.
- No presentar datos ficticios como datos reales de una mascota.
- No presentar diagnóstico, prescripción ni exclusión clínica.
- Usar datos sintéticos y cuenta Firebase de prueba.
- Mantener el worker privado y protegido por OIDC.

Definición de éxito de la demo:

```text
Dueño → objetivo/evidencia → Coordinator ADK
       → Evidence Agent → Specialist Agent → Safety Agent
       → Cloud Tasks/Cloud Run → Firestore/provenance → Android
```

Debe demostrarse una pausa `WAITING`, una reanudación, un retry idempotente y un resultado `REVIEW_REQUIRED`.

## 1. Requisitos del hackathon

- [ ] Gemini 3.5 Flash o superior en backend.
- [ ] Google ADK utilizado en runtime, no solo declarado.
- [ ] Cloud Run, Cloud Tasks y Firestore utilizados en una ejecución real.
- [ ] Categoría: `Taskmaster`.
- [ ] Arquitectura, README, testing instructions y vídeo público preparados.
- [ ] Repositorio reproducible y sin secretos.
- [ ] Vídeo de menos de cuatro minutos con prueba visible de Google Cloud.

## 2. Arquitectura objetivo

| Componente | Responsabilidad | Restricción |
|---|---|---|
| Android | Objetivo, evidencia, estados y resultados | Nunca llama Gemini ni escribe Firestore directamente |
| API Cloud Run | Auth, ownership, sesiones, runs y lectura | No bloquea trabajo largo |
| ADK Coordinator | Routing y delegación | No cambia política ni permisos |
| Evidence Agent | Calidad, modalidad y provenance | No diagnostica |
| Specialist Agent | Observaciones del dominio | No prescribe |
| Safety Agent | Incertidumbre, escalado y claims | No puede ser omitido |
| Cloud Tasks | Wake-up, retry y OIDC | Nunca invocación anónima |
| Worker Cloud Run | Ejecuta un checkpoint acotado | Privado |
| Firestore | Estado, memoria y evidencia | Acceso por backend |
| GCS | Media privada temporal | URLs efímeras |
| Evaluator offline | Feedback y candidatos | Nunca auto-promoción online |

Estados de run:

```text
CREATED → QUEUED → RUNNING → WAITING → RUNNING → COMPLETED
                         ├→ FAILED_RETRYABLE → QUEUED
                         ├→ FAILED
                         └→ CANCELLED
```

- [ ] Validar cada transición en backend.
- [ ] Persistir `step_id`, `correlation_id`, timestamps y versión.
- [ ] Impedir modificación de runs terminales.
- [ ] Reusar `run_id + step_id + idempotency_key` en retries.
- [ ] Definir causas de `WAITING`: evidencia, contexto o revisión de seguridad.

## 3. Fase A — línea base y alcance

- [x] Congelar escenario principal: PETi Check de un perro con foto/vídeo.
- [x] Definir objetivo de demo y resultado esperado.
- [x] Mantener especialistas adicionales como extensiones, no dependencias.
- [x] Ejecutar backend pytest, Ruff, mypy y `scripts/check.ps1`.
- [x] Ejecutar Android test, lint y assemble con JDK 17 disponible localmente. Todo pasa con AGP 8.13.2. Ver `docs/PHASE_A_EXECUTION_EVIDENCE.md`.
- [x] Registrar qué evidencia es fake/local y qué evidencia es cloud.
- [x] Buscar y eliminar métricas, recordatorios o “perfil completo” hardcodeados.
- [x] Verificar que una mascota nueva empieza sin salud, peso, actividad o memoria inventada.

## 4. Fase B — contratos y roster

- [ ] Definir `AgentInput`: run, sesión, owner, mascota, objetivo, refs y policy.
- [ ] Definir `AgentOutput`: step, agente, estado, observaciones, incertidumbre,
  límites, evidencia, provenance y safety state.
- [ ] Hacer obligatorios `schema_version` y `agent_version`.
- [ ] Cerrar `AgentCapability` con allowlist.
- [ ] Implementar roster:
  - [ ] `peti_orchestrator_agent`.
  - [ ] `evidence_intake_agent`.
  - [ ] `pet_specialist_agent`.
  - [ ] `safety_review_agent`.
  - [ ] `care_followup_agent`.
  - [ ] `weekly_report_agent`.
- [ ] Crear matriz agente → capability → recurso.
- [ ] Probar capability no autorizada.
- [ ] Probar acceso cross-user y cross-pet.

## 5. Fase C — Google ADK real

- [x] Declarar `google-adk`.
- [x] Crear el grafo ADK con coordinator y subagentes.
- [x] Instanciar el grafo desde `AgentExecutionService`.
- [ ] Ejecutar el flujo con `SequentialAgent` para evidence → specialist → safety.
- [ ] Usar el coordinator jerárquico para seleccionar el especialista.
- [ ] Registrar framework, agente, versión y eventos en cada checkpoint.
- [ ] Crear `AdkRunAdapter` entre `AgentRun` y sesión ADK.
- [ ] Usar `session_id` estable.
- [ ] Persistir `invocation_id` para reanudar.
- [ ] Traducir eventos ADK a checkpoints PETi.
- [ ] Preferir `run_async` en producción.
- [ ] Cubrir cancelación, timeout, provider error y redelivery.

Tools permitidas:

- [ ] `load_owned_evidence`.
- [ ] `validate_evidence_refs`.
- [ ] `read_pet_profile`.
- [ ] `write_checkpoint`.
- [ ] `request_missing_context`.
- [ ] `propose_safe_followup`.

Para todas las tools:

- [ ] Ownership viene del gateway, nunca del modelo.
- [ ] Verificar owner y mascota antes de leer/escribir.
- [ ] Devolver códigos estructurados.
- [ ] No permitir web, mensajes externos ni acciones no aprobadas.
- [ ] Probar argumentos malformados y tool poisoning.

## 6. Fase D — long-running, Cloud Tasks y recuperación

- [ ] Crear un task por checkpoint ejecutable.
- [ ] Configurar OIDC, audience, service account y worker privado.
- [ ] Definir backoff, max attempts y concurrencia.
- [ ] Hacer `task_id` determinista.
- [ ] Rechazar issuer, audience o service account incorrectos.
- [ ] Simular caída antes y después de persistir.
- [ ] Simular timeout de Gemini y Firestore.
- [ ] Garantizar que no quedan runs en `RUNNING` indefinidamente.
- [ ] Implementar reconciliador de runs atascados.
- [ ] Mostrar `last_completed_step` y `retry_count`.
- [ ] Probar redelivery sin duplicar Gemini, créditos, media ni checkpoints.
- [ ] Probar reinicio del worker y recuperación desde Firestore.

## 7. Fase E — memoria

Distinguir cuatro niveles:

1. estado de ejecución;
2. resumen de sesión y preferencias aprobadas;
3. perfil de mascota;
4. evidencia longitudinal con fuente.

- [ ] No persistir inferencias no validadas.
- [ ] Cada recuerdo incluye owner, pet, source, fecha, confianza y versión.
- [ ] Mostrar al usuario el origen del dato.
- [ ] Garantizar borrado de recuerdos y referencias al borrar cuenta.
- [ ] Probar aislamiento entre cuentas.
- [ ] Dejar vector search como opcional hasta garantizar provenance y borrado.
- [ ] Evitar conversaciones ilimitadas: usar resúmenes acotados.

## 8. Fase F — seguridad y self-evolution

- [ ] Versionar prompts e instrucciones por agente.
- [ ] Separar observación, especialista y safety review.
- [ ] Exigir incertidumbre y límites cuando la evidencia sea débil.
- [ ] Bloquear diagnosis, prescription y claims de exclusión.
- [ ] Aplicar kill switches por global/provider/model/species/operation.
- [ ] Impedir que especialista y safety agent sean el mismo paso lógico.
- [ ] Registrar decisión `SAFE_TO_DISPLAY`, `REVIEW_REQUIRED` o
  `URGENT_ESCALATION`.

Autoevolución segura:

- [ ] Registrar fallos de evaluación y feedback del revisor.
- [ ] Crear `PromptCandidate` versionado.
- [ ] Ejecutar candidatos contra dev, held-out y red-team.
- [ ] Medir utilidad, grounding, seguridad, coste y latencia.
- [ ] Rechazar candidato si empeora seguridad.
- [ ] Promover solo con aprobación explícita.
- [ ] Mantener rollback.
- [ ] Nunca modificar prompts o guardrails desde una ejecución de producción.

## 9. Fase G — API, Firestore y observabilidad

- [ ] Documentar sesiones, runs, execute, cancel, evidence, provenance y context.
- [ ] Añadir `correlation_id` en API, tasks, logs y checkpoints.
- [ ] Limitar objetivo, contexto, refs y payloads.
- [ ] Crear colecciones: `agent_sessions`, `agent_runs`,
  `agent_checkpoints`, `agent_context_requests`, `agent_actions`,
  `agent_memory`.
- [ ] Crear índices por owner, pet, state y updated_at.
- [ ] Añadir retención y borrado.
- [ ] Redactar secretos y contenido sensible en logs.
- [ ] Medir duración por agente, retries, coste y resultado de safety.
- [ ] Añadir dashboard o consulta de evidencia para la demo.

## 10. Fase H — Android y UX

Alta de mascota:

- [ ] Pantalla “Mis perros” con tarjetas y estado incompleto.
- [ ] Flujo por pasos: nombre → raza → edad/peso opcionales → confirmación.
- [ ] No rellenar datos no proporcionados.
- [ ] Explicar qué datos mejoran la personalización.
- [ ] Mostrar imagen solo si fue aportada o seleccionada por el usuario.

Agent workspace:

- [ ] Pantalla “PETi está trabajando”.
- [ ] Mostrar objetivo y mascota.
- [ ] Timeline de agentes y steps.
- [ ] Mostrar queued, running, waiting y review required.
- [ ] Permitir adjuntar evidencia solicitada.
- [ ] Mostrar cancelación, retry y última actualización.
- [ ] Mostrar provenance, incertidumbre y límites.
- [ ] Recuperar el run tras recreación o reinicio.

Look & feel:

- [ ] Fondo marfil cálido.
- [ ] Teal PETi como color primario.
- [ ] Coral/naranja para alertas y CTA.
- [ ] Tarjetas blancas redondeadas con elevación suave.
- [ ] Navegación: Inicio, Bienestar, Recordatorios, Perfil.
- [ ] Logo e iconografía coherentes con las imágenes de referencia.
- [ ] Estados vacíos útiles y sin placeholders engañosos.
- [ ] Contraste, labels, focus, TalkBack y test tags.

Integración:

- [ ] Variante internal usa Firebase Auth real.
- [ ] Variante internal usa API Cloud Run dev.
- [ ] Login email/password funciona.
- [ ] Sesión persiste tras recreación.
- [ ] Android recupera un run desde backend.
- [ ] Texto del modelo nunca se interpreta como comando de navegación.

## 11. Fase I — pruebas

Unitarias:

- [ ] contratos y schemas;
- [ ] estados y transiciones;
- [ ] ownership y capabilities;
- [ ] hash de acciones;
- [ ] idempotencia;
- [ ] policy y kill switches;
- [ ] memoria y provenance;
- [ ] safety reducer;
- [ ] adapter ADK con provider fake.

Integración local:

- [ ] sesión → run → task → checkpoint;
- [ ] delegación entre agentes;
- [ ] WAITING → context response → resume;
- [ ] retry sin duplicados;
- [ ] reinicio con Firestore emulator;
- [ ] Android contra backend fake.

Cloud dev:

- [ ] API live/ready;
- [ ] worker anónimo rechazado;
- [ ] API → Tasks OIDC;
- [ ] Tasks → worker;
- [ ] worker → Firestore;
- [ ] worker → Gemini/Vertex;
- [ ] provenance visible;
- [ ] logs sin secretos;
- [ ] límites de coste y escala a cero.

Red-team:

- [ ] prompt injection en objetivo;
- [ ] prompt injection en metadata;
- [ ] tool poisoning;
- [ ] media de otro usuario/mascota;
- [ ] JSON inválido;
- [ ] media corrupta o duplicada;
- [ ] timeout;
- [ ] solicitud de diagnóstico o medicación;
- [ ] claim “descarta X”.

## 12. Fase J — demo y entrega

Guion de cuatro minutos:

| Tiempo | Acción |
|---|---|
| 0:00–0:25 | Problema del dueño y propuesta PETi |
| 0:25–0:50 | Mascota nueva sin datos inventados |
| 0:50–1:15 | Objetivo y evidencia |
| 1:15–1:45 | Run queued |
| 1:45–2:20 | Delegación ADK |
| 2:20–2:45 | WAITING y nueva evidencia |
| 2:45–3:15 | Cloud Run, Tasks y Firestore |
| 3:15–3:40 | Safety review / REVIEW_REQUIRED |
| 3:40–4:00 | Valor y límites |

- [ ] Cuenta Firebase de prueba.
- [ ] Perro sintético.
- [ ] Media sintética estable.
- [ ] Escenario live y fallback claramente etiquetado.
- [ ] Capturas de ADK, Cloud Run, Tasks, Firestore y Android.
- [ ] Diagrama actualizado.
- [ ] Vídeo público menor de cuatro minutos.
- [ ] Verificar vídeo en incógnito.
- [ ] README con spin-up local y cloud.
- [ ] Testing instructions sin contraseña en el repositorio.
- [ ] Compartir repositorio privado con los destinatarios exigidos por Devpost.
- [ ] Añadir categoría y teammates en Devpost.
- [ ] Congelar materiales antes de la fecha límite.

## 13. Orden obligatorio de ejecución

1. Línea base y alcance.
2. Contratos y capability matrix.
3. Grafo ADK ejecutable.
4. Tools seguras y gateway.
5. Checkpoints, Tasks y resume.
6. Memoria estructurada y provenance.
7. Safety review y red-team.
8. Variante Android internal y agent workspace.
9. Tests locales completos.
10. Vertical slice real en Cloud Run.
11. Evidencia, README, diagrama y vídeo.
12. Auditoría final de secretos, costes, permisos y claims.
13. Congelación de entrega.

## 14. Criterio final de 100% operativa

- [ ] Login de prueba.
- [ ] Alta de mascota sin datos ficticios.
- [ ] Objetivo desde Android.
- [ ] Sesión/run en Firestore.
- [ ] Delegación ADK real.
- [ ] Cloud Tasks/OIDC/worker.
- [ ] Gemini estructurado.
- [ ] Safety review independiente.
- [ ] Resultado Android con provenance.
- [ ] WAITING y resume.
- [ ] Retry sin duplicados.
- [ ] Restart sin pérdida.
- [ ] Aislamiento cross-user.
- [ ] Borrado de memoria y evidencia.
- [ ] Tests críticos verdes.
- [ ] Demo con prueba visible de Google Cloud.

## Referencias

- [Hackathon](https://allthingsagentichackathon.devpost.com/)
- [Workshops y recursos](https://allthingsagentichackathon.devpost.com/resources)
- [Google ADK Python](https://github.com/google/adk-python)
- [Sistemas multiagente con ADK](https://codelabs.developers.google.com/codelabs/production-ready-ai-with-gc/3-developing-agents/build-a-multi-agent-system-with-adk?hl=en)
- [Agentes long-running con ADK](https://developers.googleblog.com/build-long-running-ai-agents-that-pause-resume-and-never-lose-context-with-adk/)
