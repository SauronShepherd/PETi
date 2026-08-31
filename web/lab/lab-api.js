const api = (path) => window.PETI_API(`/v1/internal/lab${path}`);

export class RealLabAdapter {
  async load() {
    const [access, overview, runs, agents, models, feedback, evidence, safety, performance, health, audit] = await Promise.all([
      api("/access"), api("/overview"), api("/runs?limit=100"), api("/agents"), api("/models"),
      api("/feedback?limit=100"), api("/evidence/metrics"), api("/safety/reviews"), api("/performance"), api("/health"), api("/audit"),
    ]);
    if (!access.can_view_lab) throw new Error("Esta cuenta no tiene acceso al laboratorio.");
    return {data_classification:"REAL", overview, runs:runs.items, agents:agents.items, models:models.items,
      feedback:feedback.items, evidence, safety, performance, health, audit:audit.items, run_details:{}};
  }
  async getRun(id) { return api(`/runs/${encodeURIComponent(id)}`); }
  async refreshOverview() {
    const [overview, health] = await Promise.all([api("/overview"), api("/health")]);
    return {overview, health};
  }
  async refreshRuns() { return (await api("/runs?limit=100")).items; }
}

export class DemoLabAdapter {
  async load() {
    await new Promise((resolve) => setTimeout(resolve, 150));
    const response = await fetch("demo/lab/data.json", {cache:"no-store"});
    if (!response.ok) throw new Error("No se pudo cargar el replay de laboratorio.");
    const value = await response.json();
    if (value.data_classification !== "SYNTHETIC_DEMO") throw new Error("El replay no está clasificado como sintético.");
    return value;
  }
  async getRun() { return null; }
  async refreshOverview() { return null; }
  async refreshRuns() { return null; }
}

export const createLabAdapter = (demo) => demo ? new DemoLabAdapter() : new RealLabAdapter();
