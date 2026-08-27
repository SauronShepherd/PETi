$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

# This harness is local-only: it starts no provider and does not use customer
# data. Specialist manifests are validated, then the domain safety boundary is
# exercised with fake repositories.
python scripts/build_specialist_evidence_inventory.py
if ($LASTEXITCODE -ne 0) { throw 'Specialist evaluation manifests are invalid.' }

python -m pytest backend/tests/test_specialists_phase8_10.py -q
if ($LASTEXITCODE -ne 0) { throw 'Phase 8-10 specialist local acceptance failed.' }

python eval/weekly_report/run.py --split regression --output (Join-Path $env:TEMP 'peti-phase8-11-regression.json')
if ($LASTEXITCODE -ne 0) { throw 'Deterministic regression evaluation failed.' }

Write-Host 'Local specialist Phase 8-11 acceptance passed; real Gemini/device evidence remains external.'
