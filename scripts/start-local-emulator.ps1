$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

docker compose -f infra/local/docker-compose.yml up -d
if ($LASTEXITCODE -ne 0) { throw 'Docker Desktop is required to start Floci.' }

Write-Host 'Floci GCP emulator is running on http://127.0.0.1:4588'
Write-Host 'Start the API against it with: scripts\run-local-emulator.ps1'
