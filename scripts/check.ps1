$ErrorActionPreference='Stop'
# Native commands must participate in the fail-fast gate.
$PSNativeCommandUseErrorActionPreference = $true
python -m ruff check backend
python -m mypy backend/app
python scripts/check_web.py
python -m pytest --collect-only -q
python -m pytest
python scripts/credit_lifecycle_harness.py
python scripts/architecture_check.py
python scripts/check_scope_guard.py
python -c "import json; json.load(open('contracts/foundations.json'))"
python eval/weekly_report/run.py --split dev --output (Join-Path $env:TEMP 'peti-weekly-dev.json')
python eval/weekly_report/run.py --split held_out --output (Join-Path $env:TEMP 'peti-weekly-held-out.json')
python eval/weekly_report/run.py --split red_team --output (Join-Path $env:TEMP 'peti-weekly-red-team.json')
python eval/weekly_report/run.py --split regression --output (Join-Path $env:TEMP 'peti-weekly-regression.json')
python scripts/build_specialist_evidence_inventory.py
python scripts/build_release_evidence.py
python scripts/release_gate_check.py
python scripts/check_adr_index.py
python scripts/check_traceability.py
python scripts/check_privacy_export_contract.py
python scripts/check_logging_contract.py
python scripts/check_production_config.py
python scripts/check_release_manifests.py
python scripts/check_metric_cardinality.py
python scripts/check_lab_privacy.py
python scripts/check_lab_contracts.py
python scripts/seed_lab_demo.py
python -c "import json,glob; [json.load(open(p, encoding='utf-8')) for p in glob.glob('contracts/lab/*.schema.json')]"
if (Get-Command terraform -ErrorAction SilentlyContinue) {
    $terraformDir = (Join-Path $PSScriptRoot '..\infra\terraform\modules\peti-platform')
    terraform "-chdir=$terraformDir" fmt -check
    foreach ($environment in @('sandbox', 'staging', 'production')) {
        $terraformDir = (Join-Path $PSScriptRoot "..\infra\terraform\environments\$environment")
        terraform "-chdir=$terraformDir" init -backend=false -input=false
        terraform "-chdir=$terraformDir" fmt -check
        terraform "-chdir=$terraformDir" validate
    }
}
