$ErrorActionPreference='Stop'
$root = Resolve-Path (Join-Path $PSScriptRoot '..')
$android = Join-Path $root 'android'
if (Test-Path (Join-Path $android 'gradlew.bat')) { Write-Output 'Android Gradle wrapper already present'; exit 0 }
$gradleVersion='8.13'
$zip=Join-Path $env:TEMP "gradle-$gradleVersion-bin.zip"
$dir=Join-Path $env:TEMP "gradle-$gradleVersion"
Invoke-WebRequest -Uri "https://services.gradle.org/distributions/gradle-$gradleVersion-bin.zip" -OutFile $zip
Expand-Archive -LiteralPath $zip -DestinationPath $env:TEMP -Force
& (Join-Path $dir 'bin\gradle.bat') -p $android wrapper --gradle-version $gradleVersion
Write-Output 'Android Gradle wrapper generated.'
