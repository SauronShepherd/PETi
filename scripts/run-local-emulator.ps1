$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

& (Join-Path $PSScriptRoot 'start-local-emulator.ps1')
$env:PETI_ENVIRONMENT = 'LOCAL'
$env:PETI_AUTH_MODE = 'LOCAL_TEST'
$env:PETI_STORAGE_MODE = 'FIRESTORE_EMULATOR'
$env:PETI_FIRESTORE_EMULATOR_HOST = '127.0.0.1:4588'
$env:STORAGE_EMULATOR_HOST = 'http://127.0.0.1:4588'
$env:FIRESTORE_EMULATOR_HOST = $env:PETI_FIRESTORE_EMULATOR_HOST

Set-Location (Join-Path $PSScriptRoot '..\backend')
python -m uvicorn app.main:app --reload
