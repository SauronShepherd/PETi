# Hackathon Testing Instructions

From a PowerShell terminal at the repository root:

```powershell
python -m ruff check backend
python -m mypy backend/app
python -m pytest -q
python scripts/architecture_check.py
python scripts/phase1_security_check.py
python scripts/validate_acceptance_bundle.py
```

These commands verify repository behavior with local fakes/emulators. They do
not certify Gemini, Cloud Run, Firebase, Play Console, FCM, or a physical
device. For the sandbox flow, run `infra/cloudrun/preflight.ps1` first and
record the exact model, revision, request ID, usage, safety result, and input
hash under `release/evidence/`, with no private content.
