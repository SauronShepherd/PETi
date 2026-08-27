param(
    [string]$AvdName = "dev35_default_x86_64_Pixel_2",
    [switch]$StartEmulator
)

$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $PSScriptRoot
$sdkRoot = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
$adb = Join-Path $sdkRoot 'platform-tools\adb.exe'
$emulator = Join-Path $sdkRoot 'emulator\emulator.exe'
$avdHome = Join-Path $env:USERPROFILE '.android\avd\gradle-managed'
$appApk = Join-Path $workspace 'android\app\build\outputs\apk\debug\app-debug.apk'
$testApk = Join-Path $workspace 'android\app\build\outputs\apk\androidTest\debug\app-debug-androidTest.apk'

if (!(Test-Path -LiteralPath $adb) -or !(Test-Path -LiteralPath $appApk) -or !(Test-Path -LiteralPath $testApk)) {
    throw 'Build APKs and Android SDK platform-tools are required first.'
}

if ($StartEmulator) {
    if (!(Test-Path -LiteralPath $emulator)) { throw 'Android emulator executable not found.' }
    $env:ANDROID_AVD_HOME = $avdHome
    Start-Process -FilePath $emulator -ArgumentList '-avd', $AvdName, '-no-snapshot', '-no-audio', '-no-boot-anim', '-gpu', 'swiftshader_indirect' -WindowStyle Hidden
}

$device = $null
for ($i = 0; $i -lt 60; $i++) {
    $lines = & $adb devices
    $device = $lines | Where-Object { $_ -match '^emulator-\d+\s+device$' } | Select-Object -First 1
    if ($device) { break }
    Start-Sleep -Seconds 2
}
if (!$device) { throw 'No online Android device found; start an AVD and retry.' }

& $adb install -r $appApk | Out-Host
& $adb install -r $testApk | Out-Host
$instrumentation = @(& $adb shell am instrument -w -r 'com.peti.app.debug.test/androidx.test.runner.AndroidJUnitRunner' 2>&1)
$instrumentation | Out-Host
if ($LASTEXITCODE -ne 0 -or ($instrumentation -join "`n") -match 'Process crashed|FAILURES!!!|There were [1-9][0-9]* failures') {
    throw 'AndroidX instrumentation failed or the target process crashed.'
}
Write-Host 'Manual Android instrumentation passed.'
