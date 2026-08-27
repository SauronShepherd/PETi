param([string]$Python = "python")

$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

Write-Host 'Phase 4/5 Floci local acceptance: no GCP, AWS, or Gemini network calls.'

& $Python scripts/validate_acceptance_bundle.py artifacts/phase45/acceptance_bundle.example.json
if ($LASTEXITCODE -ne 0) { throw 'Acceptance bundle validation failed.' }

& $Python eval/run.py --suite peti_check_red_team --provider fake --environment local
if ($LASTEXITCODE -ne 0) { throw 'FakeAI evaluation failed.' }

& (Join-Path $PSScriptRoot 'check.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Local build/check suite failed.' }

& (Join-Path $PSScriptRoot 'test-floci.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Floci Phase 1/2 smoke failed.' }

& (Join-Path $PSScriptRoot 'test-floci-phase3.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Floci Phase 3 smoke failed.' }

& (Join-Path $PSScriptRoot 'run-fake-peti-check.ps1') -Python $Python
if ($LASTEXITCODE -ne 0) { throw 'Fake PETi Check vertical slice failed.' }

Write-Host 'Phase 4/5 Floci local acceptance passed.'
