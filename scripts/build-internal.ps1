$ErrorActionPreference = 'Stop'

$androidRoot = Join-Path $PSScriptRoot '..\android'
Push-Location $androidRoot
try {
    & .\gradlew.bat assembleInternal bundleInternal
    if ($LASTEXITCODE -ne 0) { throw "assembleInternal/bundleInternal failed with exit code $LASTEXITCODE" }
}
finally { Pop-Location }

$outputs = @(
    (Join-Path $androidRoot 'app\build\outputs\bundle\internal\app-internal.aab'),
    (Join-Path $androidRoot 'app\build\outputs\apk\internal\app-internal.apk')
)
$found = $outputs | Where-Object { Test-Path -LiteralPath $_ }
if (-not $found) { throw 'Gradle completed but no internal AAB/APK artifact was found.' }
$found | ForEach-Object { Write-Host "INTERNAL_ARTIFACT=$((Resolve-Path -LiteralPath $_).Path)" }
