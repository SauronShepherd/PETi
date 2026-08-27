$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

docker compose -f infra/local/docker-compose.yml up -d
if ($LASTEXITCODE -ne 0) { throw 'Floci emulator could not be started.' }

$env:PETI_ENVIRONMENT = 'LOCAL'
$env:PETI_AUTH_MODE = 'LOCAL_TEST'
$env:PETI_STORAGE_MODE = 'FIRESTORE_EMULATOR'
$env:PETI_AI_PROVIDER = 'FAKE'
$env:PETI_TASK_QUEUE = 'FAKE'
$env:PETI_FIRESTORE_EMULATOR_HOST = '127.0.0.1:4588'
$env:FIRESTORE_EMULATOR_HOST = '127.0.0.1:4588'
$env:STORAGE_EMULATOR_HOST = 'http://127.0.0.1:4588'

python -m pytest backend/tests/test_phase7_records.py backend/tests/test_phase7_api_e2e.py -q
if ($LASTEXITCODE -ne 0) { throw 'Phase 7 Floci E2E failed.' }

Write-Host 'Floci Phase 7 Record Vault acceptance passed.'
