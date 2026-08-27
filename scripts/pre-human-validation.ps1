$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
Set-Location (Join-Path $PSScriptRoot '..')

Write-Host 'PETi pre-human validation: source and static gates'
python scripts/build_release_evidence.py
python scripts/check_release_manifests.py
python scripts/check_traceability.py
python scripts/check_production_config.py
python scripts/check_scope_guard.py
python scripts/check_privacy_export_contract.py
python scripts/check_logging_contract.py
python scripts/check_metric_cardinality.py
python scripts/check_billing_security.py
python scripts/architecture_check.py
python scripts/phase1_security_check.py

$artifact = Join-Path $PSScriptRoot '..\android\app\build\outputs\bundle\internal\app-internal.aab'
if (Test-Path -LiteralPath $artifact) {
    python scripts/inspect_release_artifact.py $artifact
} else {
    Write-Host 'RELEASE_ARTIFACT=NOT_BUILT; build the internal AAB before human validation.'
}

Write-Host 'PRE_HUMAN_VALIDATION=PASS_SOURCE_STATIC_ONLY'
Write-Host 'Physical-device, legal, cloud-authenticated, and reviewer gates remain external.'
