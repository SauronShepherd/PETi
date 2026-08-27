param([string]$Python = "python")

$ErrorActionPreference = "Stop"
& $Python -m pytest backend/tests/test_peti_check_fake_e2e.py -q
if ($LASTEXITCODE -ne 0) { throw "Fake PETi Check vertical slice failed." }
Write-Host "Fake PETi Check vertical slice passed."
