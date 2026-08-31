import { escapeHtml as esc, formatNumber } from "./lab-format.js";

export function horizontalBars(title, entries, {percent = false} = {}) {
  const rows = entries.filter(([, value]) => Number.isFinite(Number(value)));
  if (!rows.length) return '<div class="lab-empty">No hay datos suficientes para representar.</div>';
  const max = Math.max(...rows.map(([, value]) => Number(value)), 1);
  const description = rows.map(([label, value]) => `${label}: ${value}`).join("; ");
  return `<figure class="lab-chart"><figcaption>${esc(title)}</figcaption><svg viewBox="0 0 520 ${rows.length * 42 + 12}" role="img" aria-label="${esc(`${title}. ${description}`)}">${rows.map(([label, value], index) => {
    const number = Number(value); const y = index * 42 + 8; const width = Math.max(2, (number / max) * 310);
    const shown = percent ? `${Math.round(number * 100)}%` : formatNumber(number);
    return `<text x="0" y="${y + 15}">${esc(label)}</text><rect x="155" y="${y}" width="310" height="22" rx="7" class="lab-chart-track"/><rect x="155" y="${y}" width="${width}" height="22" rx="7" class="lab-chart-value"/><text x="475" y="${y + 15}" class="lab-chart-number">${esc(shown)}</text>`;
  }).join("")}</svg><div class="lab-chart-table" aria-hidden="true">${rows.map(([label, value]) => `<span><b>${esc(label)}</b><i>${formatNumber(value)}</i></span>`).join("")}</div></figure>`;
}
