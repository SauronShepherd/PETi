"""Fail-closed static smoke checks for the active PETi web client."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
required = {
    "index.html": ["styles.css", "app.js", 'lang="es"'],
    "styles.css": ["@media(max-width:820px)", "--teal:#009e96", ".mobile-nav"],
    "app.js": ["signInWithEmailAndPassword", "signInWithPopup", "PETi Check", "Workspace", "demoMode", "data-filter", "historyFilter", "loadTimeline", "extendedView(state.route)", "window.PETI_API = api"],
    "extended-views.js": ["route === \"CARE\"", "route === \"RECORDS\"", "route === \"ASSISTANT\"", "Cuidados", "Documentos", "Asistente grounded", "No hay documentos todavía", "No es un diagnóstico"],
    "README.md": ["Firebase Web Auth", "?demo=1"],
}
for name, needles in required.items():
    path = WEB / name
    if not path.is_file():
        raise SystemExit(f"WEB_CHECK=FAIL missing {path}")
    text = path.read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f"WEB_CHECK=FAIL {name}: missing {missing}")
js = (WEB / "app.js").read_text(encoding="utf-8")
for forbidden in ("92/100", "Hoy · 18:00", "18.5 kg"):
    if forbidden in js:
        raise SystemExit(f"WEB_CHECK=FAIL fabricated metric present: {forbidden}")
for contract in ("headers.Authorization", "/v1/pets", "/v1/pets/", "/v1/dogs/", "/v1/agent-runs/"):
    if contract not in js:
        raise SystemExit(f"WEB_CHECK=FAIL missing runtime contract: {contract}")
if "if(!state.firebase){if(demoMode)" not in js:
    raise SystemExit("WEB_CHECK=FAIL authentication fallback is not explicitly demo-gated")
print("WEB_CHECK=PASS static client, responsive tokens, Firebase auth hooks, and active routes present")
