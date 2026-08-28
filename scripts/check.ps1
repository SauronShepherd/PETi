$ErrorActionPreference='Stop'
# Native commands must participate in the fail-fast gate; without this,
# PowerShell can continue after a non-zero Python/Gradle exit code.
$PSNativeCommandUseErrorActionPreference = $true
python -m ruff check backend
python -m mypy backend/app
python -m pytest --collect-only -q
python -m pytest
python scripts/credit_lifecycle_harness.py
python scripts/architecture_check.py
python scripts/check_android_funding_module.py
python scripts/check_scope_guard.py
python -c "import json; json.load(open('contracts/foundations.json'))"
if (Test-Path (Join-Path $PSScriptRoot '..\android\gradlew.bat')) {
    if (-not $env:ANDROID_HOME) {
        $candidateSdk = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
        if (Test-Path $candidateSdk) { $env:ANDROID_HOME = $candidateSdk }
    }
    $javaMajor = 0
    $javaReleaseFile = if ($env:JAVA_HOME) { Join-Path $env:JAVA_HOME 'release' } else { $null }
    if ($javaReleaseFile -and (Test-Path $javaReleaseFile)) {
        $javaRelease = Get-Content $javaReleaseFile -Raw
        if ($javaRelease -match 'JAVA_VERSION="([0-9]+)') { $javaMajor = [int]$Matches[1] }
    }
    if ($javaMajor -lt 17 -or $javaMajor -ge 25) {
        $javaCandidates = @(
            (Get-ChildItem (Join-Path $env:ProgramFiles 'Microsoft') -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^jdk-(17|18|19|20|21|22|23|24)' } | Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty FullName),
            'C:\Program Files\Android\Android Studio\jbr'
        ) | Where-Object { $_ -and (Test-Path (Join-Path $_ 'bin\java.exe')) }
        foreach ($candidate in $javaCandidates) {
            $candidateRelease = Join-Path $candidate 'release'
            if (Test-Path $candidateRelease) {
                $candidateText = Get-Content $candidateRelease -Raw
                if ($candidateText -match 'JAVA_VERSION="([0-9]+)') {
                    $candidateMajor = [int]$Matches[1]
                    if ($candidateMajor -ge 17 -and $candidateMajor -lt 25) {
                        $env:JAVA_HOME = $candidate
                        $env:Path = "$candidate\bin;" + (($env:Path -split ';' | Where-Object { $_ -notmatch 'Java|jdk-|Android Studio\\Android Studio\\jbr' }) -join ';')
                        Write-Host "Using compatible JDK for Gradle: $candidate"
                        break
                    }
                }
            }
        }
    }
    Push-Location (Join-Path $PSScriptRoot '..\android')
    try {
        if (-not $env:JAVA_TOOL_OPTIONS) {
            $env:JAVA_TOOL_OPTIONS = '-Djdk.net.unixdomain.tmpdir=C:\Temp\peti-java-sockets'
        }
        .\gradlew.bat test lint assembleDebug
        if ($LASTEXITCODE -ne 0) { throw "Gradle verification failed with exit code $LASTEXITCODE" }
        if ($env:PETI_RELEASE_API_BASE_URL -and $env:PETI_GOOGLE_WEB_CLIENT_ID) {
            .\gradlew.bat assembleRelease
            if ($LASTEXITCODE -ne 0) { throw "Gradle release build failed with exit code $LASTEXITCODE" }
        } else {
            Write-Host 'Skipping assembleRelease: PETI_RELEASE_API_BASE_URL and PETI_GOOGLE_WEB_CLIENT_ID are external release inputs.'
        }
    }
    finally { Pop-Location }
} else { throw 'Android Gradle wrapper is missing. Run scripts/bootstrap.ps1 first.' }
python scripts/phase1_security_check.py
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
python scripts/check_billing_security.py
python scripts/check_production_config.py
python scripts/check_release_manifests.py
python scripts/check_play_worksheets.py
python scripts/check_metric_cardinality.py
python scripts/inspect_release_artifact.py
if (Get-Command terraform -ErrorAction SilentlyContinue) {
    $terraformDir = (Join-Path $PSScriptRoot '..\infra\terraform\modules\peti-platform')
    terraform "-chdir=$terraformDir" fmt -check
    $sandboxTerraformDir = (Join-Path $PSScriptRoot '..\infra\terraform\environments\sandbox')
    terraform "-chdir=$sandboxTerraformDir" init -backend=false -input=false
    terraform "-chdir=$sandboxTerraformDir" fmt -check
    terraform "-chdir=$sandboxTerraformDir" validate
}
