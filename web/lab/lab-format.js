export const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[char]));
export const formatPercent = (value) => value == null ? "Sin datos" : new Intl.NumberFormat(document.documentElement.lang || "es", {style:"percent", maximumFractionDigits:0}).format(value);
export const formatNumber = (value) => value == null ? "Desconocido" : new Intl.NumberFormat(document.documentElement.lang || "es").format(value);
export const formatDuration = (value) => value == null ? "En curso" : value < 1000 ? `${value} ms` : `${(value / 1000).toFixed(1)} s`;
