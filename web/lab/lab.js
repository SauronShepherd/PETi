import { createLabAdapter } from "./lab-api.js";
import { horizontalBars } from "./lab-charts.js";
import { escapeHtml as esc, formatDuration, formatNumber, formatPercent } from "./lab-format.js";
import { navigateLab, readLabRoute } from "./lab-router.js";
import { getState as getLabState, reset as resetLabState, setState as setLabState } from "./lab-state.js";

const demoMode = () => new URLSearchParams(location.search).get("demo") === "1";
const labels = {
  SAFETY_ROUTED:{es:"Derivado por seguridad",en:"Safety routed"}, SAFE_TO_DISPLAY:{es:"Seguro para mostrar",en:"Safe to display"},
  REVIEW_REQUIRED:{es:"Revisión necesaria",en:"Review required"}, POLICY_BLOCKED:{es:"Bloqueado por política",en:"Policy blocked"},
  NO_CLEAR_NEXT_STEP:{es:"Sin siguiente paso claro",en:"No clear next step"}, TOO_SLOW:{es:"Respuesta demasiado lenta",en:"Response too slow"},
  NOT_QUITE:{es:"No del todo",en:"Not quite"}, HELPED:{es:"Me ayudó",en:"Helped"},
};
const humanLabel = (value) => {
  const item = labels[String(value || "").toUpperCase()];
  return item ? item[document.documentElement.lang === "en" ? "en" : "es"] : String(value || "").replaceAll("_", " ");
};

const views = [
  ["COMMAND", "Command Center", "⌁"], ["RUNS", "Live Runs", "◉"],
  ["AGENTS", "Agent Laboratory", "✤"], ["MODELS", "Model Intelligence", "◇"],
  ["EVIDENCE", "Evidence Lab", "▧"], ["FEEDBACK", "User Feedback", "♡"],
  ["SAFETY", "Safety & Evals", "⬡"], ["COST", "Performance & Cost", "⌇"],
  ["HEALTH", "System Health", "◎"], ["AUDIT", "Audit & Governance", "▤"],
];

let data = null;
let currentView = "COMMAND";
let selectedRun = null;
let root = null;
let requestController = null;
let adapter = null;
let pollTimer = null;
let pollInFlight = false;
let pollFailures = 0;
let mounted = false;
let runTab = "OVERVIEW";
let runFilters = {run:"ALL", page:1};
const RUN_PAGE_SIZE = 10;

function metric(label, item, tone="") {
  const value = item?.value;
  const interval = item?.ci95?.low == null ? "" : `IC95 ${formatPercent(item.ci95.low)}–${formatPercent(item.ci95.high)}`;
  return `<article class="lab-metric ${tone}"><span>${esc(label)}</span><strong>${formatPercent(value)}</strong><small>${item?.denominator != null ? `${item.numerator}/${item.denominator}` : "Cobertura desconocida"}${interval ? ` · ${interval}` : ""}${item?.preliminary ? " · preliminar" : ""}</small></article>`;
}

function statusBadge(status) {
  const normalized = String(status || "UNKNOWN").toUpperCase();
  const tone = /FAIL|ERROR|UNSAFE/.test(normalized) ? "danger" : /REVIEW|WAIT|ROUTED|UNKNOWN|NOT_/.test(normalized) ? "warning" : "success";
  return `<span class="lab-status ${tone}">${esc(humanLabel(normalized))}</span>`;
}

function commandCenter() {
  const overview = data.overview;
  const metrics = overview.metrics || {};
  const rufs = metrics.rufs || {value:null, numerator:0, denominator:0, preliminary:true};
  const runStates = Object.entries(overview.runs_by_state || {}).map(([key,value]) => `<div><b>${formatNumber(value)}</b><span>${esc(key)}</span></div>`).join("");
  return `<div class="lab-hero"><div><span class="lab-kicker">Veterinary intelligence observatory</span><h1>Multi-Agent Mission Control</h1><p>Utilidad, evidencia y seguridad conectadas a cada ejecución.</p></div><div class="lab-rufs"><span>RUFS</span><strong>${formatPercent(rufs.value)}</strong><small>Resoluciones útiles, fundamentadas y seguras</small></div></div>
  <section class="lab-metric-grid">${metric("Utilidad", metrics.helpfulness)}${metric("Fundamentación", metrics.grounded)}${metric("Seguridad", metrics.safe_completion, "safe")}${metric("Feedback coverage", metrics.feedback_coverage)}</section>
  <div class="lab-two"><section class="lab-panel"><div class="lab-panel-head"><div><span>Live topology</span><h2>Flujo multiagente</h2></div>${statusBadge("SYSTEM HEALTHY")}</div><div class="lab-topology"><div class="lab-node active"><i>01</i><b>Orchestrator</b><small>Planifica</small></div><span>→</span><div class="lab-node active"><i>02</i><b>Evidence Intake</b><small>5 fuentes</small></div><span>→</span><div class="lab-node active"><i>03</i><b>Pet Specialist</b><small>Gemini</small></div><span>→</span><div class="lab-node review"><i>04</i><b>Safety Review</b><small>Calibra</small></div></div></section>
  <section class="lab-panel"><div class="lab-panel-head"><div><span>Run states</span><h2>Actividad</h2></div><b>${formatNumber(overview.run_count)} runs</b></div><div class="lab-state-strip">${runStates || "<p>Sin actividad registrada.</p>"}</div></section></div>
  <section class="lab-panel"><div class="lab-panel-head"><div><span>Learning loop</span><h2>Dónde aprender ahora</h2></div><button class="lab-link" data-lab-view="FEEDBACK">Abrir feedback →</button></div><div class="lab-opportunities"><article><b>Claridad del siguiente paso</b><p>La principal señal negativa aparece cuando una respuesta segura no explica qué hacer después.</p><span>Impacto alto · señal explícita</span></article><article><b>Context caching</b><p>El modelo challenger reduce tokens de entrada manteniendo las gates de seguridad.</p><span>Shadow · todavía no concluyente</span></article><article><b>Evidencia multimodal</b><p>La cobertura visual es alta; audio y vídeo necesitan una muestra mayor.</p><span>Muestra preliminar</span></article></div></section>`;
}

function runsView() {
  const feedbackByRun = new Map((data.feedback || []).map((item) => [item.run_id, item.value]));
  const selected = (data.runs || []).filter((run) => ({
    ALL:true,
    RUNNING:run.status === "STARTED",
    FAILED:run.status === "FAILED",
    SAFETY:run.safety_state === "REVIEW_REQUIRED" || run.outcome === "SAFETY_ROUTED",
    NEGATIVE:feedbackByRun.get(run.run_id) === "NOT_QUITE",
    SLOW:(run.duration_ms || 0) >= 3000,
  })[runFilters.run] ?? true);
  const pageCount = Math.max(1, Math.ceil(selected.length / RUN_PAGE_SIZE));
  const page = Math.min(runFilters.page, pageCount);
  const visible = selected.slice((page - 1) * RUN_PAGE_SIZE, page * RUN_PAGE_SIZE);
  const rows = visible.map((run) => `<tr><td><button class="lab-run-link" data-run-id="${esc(run.run_id)}">${esc(run.run_id)}</button></td><td>${statusBadge(run.status)}</td><td>${esc(humanLabel(run.outcome || "Pendiente"))}</td><td>${statusBadge(run.safety_state)}</td><td>${formatDuration(run.duration_ms)}</td></tr>`).join("");
  const filters = [["ALL","Todos"],["RUNNING","Running"],["FAILED","Failed"],["SAFETY","Safety"],["NEGATIVE","Feedback negativo"],["SLOW","Slow ≥ 3 s"]];
  return `<section class="lab-panel"><div class="lab-panel-head"><div><span>Live observatory</span><h1>Agent runs</h1></div><div class="lab-live"><i></i> actualización activa</div></div><div class="lab-run-filters" role="group" aria-label="Filtros de runs">${filters.map(([key,label]) => `<button class="${runFilters.run === key ? "active" : ""}" aria-pressed="${runFilters.run === key}" data-run-filter="${key}">${label}</button>`).join("")}</div><div class="lab-table-wrap"><table class="lab-table"><thead><tr><th>Run</th><th>Estado</th><th>Resultado</th><th>Seguridad</th><th>Duración</th></tr></thead><tbody>${rows || '<tr><td colspan="5">No hay runs para este filtro.</td></tr>'}</tbody></table></div><div class="lab-pagination"><span>${formatNumber(selected.length)} runs · página ${page}/${pageCount}</span><div><button data-run-page="${page - 1}" ${page <= 1 ? "disabled" : ""}>← Anterior</button><button data-run-page="${page + 1}" ${page >= pageCount ? "disabled" : ""}>Siguiente →</button></div></div></section>`;
}

function runInspector(runId) {
  const run = (data.runs || []).find((item) => item.run_id === runId);
  const detail = data.run_details?.[runId];
  if (!run || !detail) return `<section class="lab-panel"><button class="lab-link" data-lab-view="RUNS">← Volver</button><h1>Run inspector</h1><p>El detalle no está disponible en este dataset.</p></section>`;
  const steps = (detail.steps || []).map((step, index) => `<div class="lab-step"><i>${String(index + 1).padStart(2,"0")}</i><div><b>${esc(step.agent_id)}</b><span>${esc(step.step_id)}</span></div>${statusBadge(step.status)}<small>${formatDuration(step.duration_ms)} · ${formatNumber(step.evidence_count)} evidencias · ${formatNumber(step.claim_count)} claims</small></div>`).join("");
  const calls = (detail.model_calls || []).map((call) => `<article class="lab-call"><div><span>${esc(call.provider)}</span><h3>${esc(call.model_id)}</h3></div>${statusBadge(call.status)}<dl><div><dt>Latencia</dt><dd>${formatDuration(call.latency_ms)}</dd></div><div><dt>Input</dt><dd>${formatNumber(call.input_tokens)}</dd></div><div><dt>Output</dt><dd>${formatNumber(call.output_tokens)}</dd></div><div><dt>Cache</dt><dd>${formatNumber(call.cached_input_tokens)}</dd></div></dl></article>`).join("");
  const tools = (detail.tool_calls || []).map((tool) => `<article class="lab-call"><div><span>TOOL</span><h3>${esc(tool.tool_id)}</h3></div>${statusBadge(tool.status)}<p>${esc(tool.result_code || "Outcome unknown")} · ${formatDuration(tool.duration_ms)}</p></article>`).join("");
  const evidenceRows = (detail.evidence_usage || []).length ? detail.evidence_usage : (detail.steps || []).filter((step) => step.evidence_count || step.claim_count).map((step) => ({step_id:step.step_id, modality:"MULTIMODAL", selected_count:step.evidence_count, claim_count:step.claim_count}));
  const safetyRows = (detail.safety_decisions || []).length ? detail.safety_decisions : (detail.steps || []).filter((step) => step.safety_state).map((step) => ({step_id:step.step_id, decision:step.safety_state, policy_version:"demo-v1"}));
  const tabs = [["OVERVIEW","Overview"],["TIMELINE","Timeline"],["EVIDENCE","Evidence & claims"],["MODELS","Models & tools"],["SAFETY","Safety"],["FEEDBACK","Feedback"],["VERSIONS","Versions"]];
  const panels = {
    OVERVIEW:`<div class="lab-two"><section class="lab-panel"><h2>Execution timeline</h2><div class="lab-steps">${steps}</div></section><section class="lab-panel"><h2>Resultado y feedback</h2><div class="lab-result"><span>Response</span><b>${esc(detail.response?.id || "Pendiente")}</b>${statusBadge(detail.response?.outcome)}<p>Feedback: <strong>${esc(humanLabel(detail.feedback?.value || "Sin valoración"))}</strong></p><p>${esc((detail.feedback?.reasons || []).map(humanLabel).join(" · "))}</p></div></section></div><section class="lab-panel"><div class="lab-panel-head"><div><span>Model intelligence</span><h2>Llamadas del run</h2></div></div><div class="lab-call-grid">${calls || "Sin llamadas registradas"}</div></section>`,
    TIMELINE:`<section class="lab-panel"><h2>Deterministic execution timeline</h2><div class="lab-steps">${steps}</div></section>`,
    EVIDENCE:`<section class="lab-panel"><h2>Evidence & claims</h2><div class="lab-gates">${evidenceRows.map((item) => `<article><span>${esc(item.step_id)} · ${esc(item.modality)}</span><b>${formatNumber(item.selected_count)} / ${formatNumber(item.claim_count)} claims</b></article>`).join("") || '<div class="lab-empty">No evidence usage recorded.</div>'}</div></section>`,
    MODELS:`<section class="lab-panel"><h2>Models & tools</h2><div class="lab-call-grid">${calls}${tools || '<div class="lab-empty">No tool calls recorded.</div>'}</div></section>`,
    SAFETY:`<section class="lab-panel"><h2>Safety decisions</h2><div class="lab-gates">${safetyRows.map((item) => `<article><span>${esc(item.step_id)} · ${esc(item.policy_version)}</span>${statusBadge(item.decision)}</article>`).join("") || '<div class="lab-empty">No safety decisions recorded.</div>'}</div></section>`,
    FEEDBACK:`<section class="lab-panel"><h2>User feedback</h2><div class="lab-result">${statusBadge(detail.feedback?.value || "NOT RATED")}<p>${esc((detail.feedback?.reasons || []).map(humanLabel).join(" · ") || "No reasons")}</p></div></section>`,
    VERSIONS:`<section class="lab-panel"><h2>Frozen version set</h2><pre class="lab-version-set">${esc(JSON.stringify({agents:detail.response?.agent_version_set || {}, models:detail.response?.model_version_set || detail.model_calls?.map((item) => ({provider:item.provider, model:item.model_id})) || []}, null, 2))}</pre></section>`,
  };
  return `<button class="lab-link" data-lab-view="RUNS">← Live runs</button><div class="lab-inspector-head"><div><span>Run inspector</span><h1>${esc(run.run_id)}</h1><p>${esc(humanLabel(run.outcome || "En curso"))} · ${formatDuration(run.duration_ms)}</p></div>${statusBadge(run.safety_state)}</div><div class="lab-inspector-tabs" role="tablist" aria-label="Run inspector sections">${tabs.map(([key,label]) => `<button role="tab" aria-selected="${runTab === key}" class="${runTab === key ? "active" : ""}" data-run-tab="${key}">${label}</button>`).join("")}</div>${panels[runTab] || panels.OVERVIEW}`;
}

function agentsView() {
  return `<section class="lab-panel"><div class="lab-panel-head"><div><span>Agent roster</span><h1>Agent Laboratory</h1></div><b>${formatNumber(data.agents?.length)} contratos</b></div><div class="lab-card-grid">${(data.agents || []).map((agent) => `<article class="lab-agent"><div><span>AGENT</span>${statusBadge(agent.activity_status)}</div><h2>${esc(agent.agent_id)}</h2><p>${esc((agent.capabilities || []).join(" · "))}</p><dl><div><dt>Runs</dt><dd>${formatNumber(agent.run_count)}</dd></div><div><dt>Helpfulness</dt><dd>${formatPercent(agent.helpfulness)}</dd></div></dl></article>`).join("")}</div></section>`;
}

function modelsView() {
  return `<section class="lab-panel"><div class="lab-panel-head"><div><span>Champion / challenger</span><h1>Model Intelligence</h1></div><small>Los IDs proceden de la traza real</small></div><div class="lab-card-grid">${(data.models || []).map((model, index) => `<article class="lab-model ${index === 0 ? "champion" : ""}"><div><span>${index === 0 ? "CHAMPION" : esc(model.release_state || "OBSERVED")}</span>${statusBadge(model.unknown_usage_count ? "USAGE PARTIAL" : "USAGE KNOWN")}</div><h2>${esc(model.model_id)}</h2><p>${esc(model.provider)} · ${formatNumber(model.call_count)} llamadas</p><dl><div><dt>Helpfulness</dt><dd>${formatPercent(model.helpfulness)}</dd></div><div><dt>Latencia media</dt><dd>${formatDuration(model.average_latency_ms)}</dd></div><div><dt>Input tokens</dt><dd>${formatNumber(model.input_tokens)}</dd></div><div><dt>Output tokens</dt><dd>${formatNumber(model.output_tokens)}</dd></div></dl></article>`).join("") || '<div class="lab-empty">Todavía no hay llamadas de modelo.</div>'}</div></section>`;
}

function evidenceView() {
  const evidence = data.evidence || {};
  const modalities = Object.entries(evidence.modalities || {});
  return `<div class="lab-hero compact"><div><span class="lab-kicker">Sample & provenance observatory</span><h1>Evidence Lab</h1><p>Medios procesados, claims y cobertura sin exponer contenido.</p></div><div class="lab-rufs"><span>Grounded claims</span><strong>${formatPercent(evidence.grounded_claim_rate?.value)}</strong><small>${formatNumber(evidence.grounded_claim_count)}/${formatNumber(evidence.claim_count)} claims</small></div></div><section class="lab-metric-grid">${modalities.map(([key,value]) => `<article class="lab-metric"><span>${esc(key)}</span><strong>${formatNumber(value)}</strong><small>evidencias procesadas</small></article>`).join("")}</section><section class="lab-panel">${horizontalBars("Evidence by modality", modalities)}</section>`;
}

function feedbackView() {
  const items = data.feedback || [];
  const positive = items.filter((item) => item.value === "HELPED").length;
  const reasonCounts = Object.entries(items.flatMap((item) => item.reasons || []).reduce((counts, reason) => ({...counts, [humanLabel(reason)]:(counts[humanLabel(reason)] || 0) + 1}), {}));
  return `<div class="lab-hero compact"><div><span class="lab-kicker">Voice of the caregiver</span><h1>User Experience & Feedback</h1><p>La satisfacción es una señal de producto, no una prueba clínica.</p></div><div class="lab-rufs"><span>Esta muestra</span><strong>${formatPercent(items.length ? positive/items.length : null)}</strong><small>${formatNumber(items.length)} valoraciones visibles</small></div></div><div class="lab-two"><section class="lab-panel"><h2>Feedback correlacionado</h2><div class="lab-feedback-list">${items.map((item) => `<article><div>${statusBadge(item.value)}<b>${esc(item.run_id)}</b></div><p>${esc((item.reasons || []).map(humanLabel).join(" · ") || "Sin motivos")}</p><button class="lab-link" data-run-id="${esc(item.run_id)}">Abrir traza →</button></article>`).join("") || '<div class="lab-empty">Aún no hay feedback.</div>'}</div></section><section class="lab-panel">${horizontalBars("Feedback reasons", reasonCounts)}</section></div>`;
}

function safetyView() {
  const safety = data.safety || {};
  return `<section class="lab-panel"><div class="lab-panel-head"><div><span>Safety release gates</span><h1>Safety & Evals</h1></div>${statusBadge(safety.review_required_count ? `${safety.review_required_count} REVIEW` : "CLEAR")}</div><div class="lab-gates">${(safety.critical_gates || []).map((gate) => `<article><span>${esc(gate.gate.replaceAll("_"," "))}</span>${statusBadge(gate.status)}</article>`).join("")}</div><div class="lab-notice"><b>Release rule</b><p>Ningún challenger se promociona si falla una gate crítica, aunque mejore coste o satisfacción.</p></div></section>`;
}

function costView() {
  const perf = data.performance || {};
  return `<div class="lab-hero compact"><div><span class="lab-kicker">Efficiency observatory</span><h1>Performance & Cost</h1><p>Coste y velocidad siempre unidos a calidad y seguridad.</p></div><div class="lab-rufs"><span>Latencia modelo</span><strong>${formatDuration(perf.average_model_latency_ms)}</strong><small>media observada</small></div></div><section class="lab-metric-grid"><article class="lab-metric"><span>Model calls</span><strong>${formatNumber(perf.model_call_count)}</strong><small>${formatNumber(perf.run_count)} runs</small></article><article class="lab-metric"><span>Input tokens</span><strong>${formatNumber(perf.input_tokens)}</strong><small>uso acumulado</small></article><article class="lab-metric"><span>Output tokens</span><strong>${formatNumber(perf.output_tokens)}</strong><small>uso acumulado</small></article><article class="lab-metric"><span>Coste</span><strong>${perf.estimated_cost_microunits == null ? "Desconocido" : formatNumber(perf.estimated_cost_microunits)}</strong><small>${esc(perf.cost_status || "UNKNOWN")} · microunidades</small></article></section>`;
}

function healthView() {
  const health = data.health || {};
  return `<section class="lab-panel"><div class="lab-panel-head"><div><span>Observability health</span><h1>System Health</h1></div>${statusBadge(health.status)}</div><div class="lab-health"><article><span>Telemetry events</span><b>${formatNumber(health.telemetry_event_count)}</b></article><article><span>Run traces</span><b>${formatNumber(health.trace_count)}</b></article><article><span>Model traces</span><b>${formatNumber(health.model_call_trace_count)}</b></article><article><span>Freshness</span><b>${esc(health.data_freshness || "UNKNOWN")}</b></article><article><span>Trace completeness</span><b>${formatPercent(health.trace_completeness_rate?.value)}</b></article><article><span>Orphan traces</span><b>${formatNumber(health.orphan_trace_count)}</b></article><article><span>Rollup lag</span><b>${health.rollup_lag_seconds == null ? "UNKNOWN" : formatDuration(health.rollup_lag_seconds * 1000)}</b></article><article><span>Dropped telemetry</span><b>${formatNumber(health.telemetry_events_dropped)}</b></article></div></section>`;
}

function auditView() {
  const rows = (data.audit || []).map((item) => `<tr><td>${esc(item.action)}</td><td>${esc(item.target_type)}</td><td>${statusBadge(item.outcome)}</td><td>${esc(item.occurred_at || "")}</td></tr>`).join("");
  return `<section class="lab-panel"><div class="lab-panel-head"><div><span>Governance ledger</span><h1>Audit & Governance</h1></div>${statusBadge(demoMode() ? "DEMO READ ONLY" : "READ ONLY")}</div><div class="lab-notice"><b>Privacy by construction</b><p>Esta vista no muestra chain-of-thought, secretos, URLs firmadas ni payloads de usuario. Los accesos a contenido sensible requieren un permiso adicional y quedan auditados.</p></div>${rows ? `<div class="lab-table-wrap"><table class="lab-table"><thead><tr><th>Acción</th><th>Objetivo</th><th>Resultado</th><th>Fecha</th></tr></thead><tbody>${rows}</tbody></table></div>` : '<div class="lab-empty"><b>Sin eventos de auditoría</b><span>Los accesos sensibles aparecerán aquí de forma pseudonimizada.</span></div>'}<div class="lab-empty"><b>Sin mutaciones administrativas</b><span>Promoción, rollback y kill switches permanecen fuera de esta consola read-only.</span></div></section>`;
}

function content() {
  if (selectedRun) return runInspector(selectedRun);
  return ({COMMAND:commandCenter, RUNS:runsView, AGENTS:agentsView, MODELS:modelsView, EVIDENCE:evidenceView, FEEDBACK:feedbackView, SAFETY:safetyView, COST:costView, HEALTH:healthView, AUDIT:auditView}[currentView] || commandCenter)();
}

function render() {
  if (!root || !data) return;
  const runtime = getLabState();
  const warning = runtime.errors?.polling
    ? '<div class="lab-runtime-warning" role="status"><b>Actualización pausada</b><span>Conservamos los últimos datos válidos y reintentaremos automáticamente.</span></div>'
    : data.health?.data_freshness === "STALE"
      ? '<div class="lab-runtime-warning" role="status"><b>Datos atrasados</b><span>Comprueba la salud de telemetría antes de tomar decisiones.</span></div>' : "";
  root.innerHTML = `<div class="peti-lab">${demoMode() ? '<div class="lab-demo-banner"><b>Demo data</b><span>Synthetic replay · no representa usuarios ni tráfico real</span></div>' : ""}${warning}<div class="lab-layout"><aside class="lab-nav"><div class="lab-brand"><span>✣</span><div><b>PETi Veterinary AI Lab</b><small>Multi-Agent Mission Control</small></div></div><nav>${views.map(([key,label,icon]) => `<button class="${!selectedRun && currentView === key ? "active" : ""}" data-lab-view="${key}"><i>${icon}</i>${label}</button>`).join("")}</nav><div class="lab-nav-foot"><i></i><span>Telemetry ${esc(data.health?.data_freshness || "connected")}</span></div></aside><main class="lab-main">${content()}</main></div></div>`;
  root.querySelector(".lab-nav")?.setAttribute("aria-label", "Veterinary AI Lab");
  root.querySelector(".lab-main")?.setAttribute("tabindex", "-1");
  root.querySelectorAll("[data-lab-view]").forEach((button) => {
    if (button.classList.contains("active")) button.setAttribute("aria-current", "page");
    button.addEventListener("click", () => navigateLab(button.dataset.labView));
  });
  root.querySelectorAll("[data-run-id]").forEach((button) => button.addEventListener("click", async () => {
    navigateLab("RUNS", button.dataset.runId);
  }));
  root.querySelectorAll("[data-run-tab]").forEach((button) => button.addEventListener("click", () => {
    runTab = button.dataset.runTab;
    render();
    root?.querySelector(`[data-run-tab="${runTab}"]`)?.focus();
  }));
  root.querySelectorAll("[data-run-filter]").forEach((button) => button.addEventListener("click", () => {
    runFilters = {run:button.dataset.runFilter, page:1};
    navigateLab("RUNS", null, runFilters);
  }));
  root.querySelectorAll("[data-run-page]").forEach((button) => button.addEventListener("click", () => {
    if (button.disabled) return;
    runFilters = {...runFilters, page:Number(button.dataset.runPage)};
    navigateLab("RUNS", null, runFilters);
  }));
}

function stopPolling() {
  if (pollTimer) clearTimeout(pollTimer);
  pollTimer = null;
}

function schedulePolling() {
  stopPolling();
  if (!mounted || demoMode() || document.hidden || !["COMMAND", "RUNS"].includes(currentView)) return;
  const intervals = window.PETI_LAB_POLL_INTERVALS || {runs:5000, command:15000};
  const base = currentView === "RUNS" ? intervals.runs : intervals.command;
  const delay = Math.min(60000, base * (2 ** pollFailures));
  pollTimer = setTimeout(refreshCurrentView, delay);
}

async function refreshCurrentView() {
  if (pollInFlight || !mounted || document.hidden || !adapter) return schedulePolling();
  pollInFlight = true;
  try {
    if (currentView === "RUNS") data.runs = await adapter.refreshRuns();
    else if (currentView === "COMMAND") Object.assign(data, await adapter.refreshOverview());
    pollFailures = 0;
    setLabState({data, pollingPaused:false, errors:{}});
    render();
  } catch (error) {
    pollFailures += 1;
    setLabState({errors:{polling:error.message}, pollingPaused:false});
    if (/401|403/.test(String(error.message))) {
      data = null;
      stopPolling();
      if (root) root.innerHTML = '<div class="lab-restricted"><span>⬡</span><h1>Sesión caducada</h1><p>Vuelve a autenticarte para consultar el laboratorio.</p></div>';
      return;
    }
  } finally {
    pollInFlight = false;
  }
  schedulePolling();
}

async function syncRoute({focus = true} = {}) {
  const route = readLabRoute();
  if (!route) return unmountLab();
  currentView = route.route;
  if (route.route === "RUNS" && !route.runId) runFilters = route.filters || {run:"ALL", page:1};
  if (selectedRun !== route.runId) runTab = "OVERVIEW";
  selectedRun = route.runId;
  if (selectedRun && data && !data.run_details?.[selectedRun]) {
    try { data.run_details[selectedRun] = await adapter.getRun(selectedRun); }
    catch (_) { data.run_details[selectedRun] = null; }
  }
  setLabState({route:currentView, selectedRunId:selectedRun});
  render();
  if (focus) root?.querySelector(".lab-main")?.focus();
  schedulePolling();
}

export async function mountLab() {
  root = document.querySelector("#peti-lab-root");
  if (!root) return;
  mounted = true;
  if (requestController) requestController.abort();
  requestController = new AbortController();
  stopPolling();
  adapter = createLabAdapter(demoMode());
  resetLabState();
  setLabState({demo:demoMode(), loading:{initial:true}});
  root.innerHTML = '<div class="lab-loading"><i></i><b>Preparando Veterinary AI Lab…</b><span>Validando permisos y trazas.</span></div>';
  try {
    data = await adapter.load();
    setLabState({data, loading:{}, errors:{}});
    await syncRoute({focus:false});
  } catch (error) {
    data = null;
    setLabState({loading:{}, errors:{initial:error.message}});
    root.innerHTML = `<div class="lab-restricted"><span>⬡</span><h1>Laboratorio protegido</h1><p>${esc(error.message || "No se pudo abrir el laboratorio.")}</p><small>La demo pública está disponible en <code>/?demo=1#ADMIN/COMMAND_CENTER</code>.</small></div>`;
  }
}

export function unmountLab() {
  mounted = false;
  stopPolling();
  requestController?.abort();
  requestController = null;
  root = null;
  data = null;
  adapter = null;
  resetLabState();
}

window.addEventListener("hashchange", () => { if (mounted) syncRoute(); });
document.addEventListener("visibilitychange", () => {
  setLabState({pollingPaused:document.hidden});
  if (document.hidden) stopPolling(); else schedulePolling();
});
