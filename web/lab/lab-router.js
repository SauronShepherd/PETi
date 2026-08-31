const ROUTES = new Set(["COMMAND", "RUNS", "AGENTS", "MODELS", "EVIDENCE", "FEEDBACK", "SAFETY", "COST", "HEALTH", "AUDIT"]);

export function readLabRoute() {
  const [path, query = ""] = location.hash.replace(/^#/, "").split("?", 2);
  const segments = path.split("/").filter(Boolean);
  if (segments[0]?.toUpperCase() !== "ADMIN") return null;
  const raw = (segments[1] || "COMMAND_CENTER").toUpperCase();
  const requested = raw === "COMMAND_CENTER" ? "COMMAND" : raw;
  if (requested === "RUNS" && segments[2]) {
    const runId = decodeURIComponent(segments.slice(2).join("/")).slice(0, 128);
    return {route: "RUNS", runId, filters: {}};
  }
  const params = new URLSearchParams(query);
  return {
    route: ROUTES.has(requested) ? requested : "COMMAND",
    runId: null,
    filters: {
      run: ["ALL", "RUNNING", "FAILED", "SAFETY", "NEGATIVE", "SLOW"].includes(params.get("filter")) ? params.get("filter") : "ALL",
      page: Math.max(1, Math.min(999, Number(params.get("page")) || 1)),
    },
  };
}

export function navigateLab(route, runId = null, filters = null) {
  const safeRoute = ROUTES.has(route) ? route : "COMMAND";
  const suffix = runId ? `/${encodeURIComponent(String(runId).slice(0, 128))}` : "";
  const routeSegment = safeRoute === "COMMAND" ? "COMMAND_CENTER" : safeRoute;
  const query = !runId && safeRoute === "RUNS" && filters
    ? `?filter=${encodeURIComponent(filters.run || "ALL")}&page=${Math.max(1, Number(filters.page) || 1)}`
    : "";
  const next = `ADMIN/${routeSegment}${suffix}${query}`;
  if (location.hash.slice(1) === next) window.dispatchEvent(new HashChangeEvent("hashchange"));
  else location.hash = next;
}
