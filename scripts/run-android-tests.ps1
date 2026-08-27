param(
    [switch]$ManagedDevice
)

$ErrorActionPreference='Stop'
Set-Location (Join-Path $PSScriptRoot '..\android')
if (-not (Test-Path '.\gradlew.bat')) { throw 'Android Gradle wrapper is missing. Run scripts/bootstrap.ps1 first.' }

# Gradle requires a supported JDK. Prefer the installed Microsoft JDK used by
# the release gate over a machine-wide JAVA_HOME that may point to JDK 11.
$javaMajor = 0
$javaReleaseFile = if ($env:JAVA_HOME) { Join-Path $env:JAVA_HOME 'release' } else { $null }
if ($javaReleaseFile -and (Test-Path $javaReleaseFile)) {
    $javaRelease = Get-Content $javaReleaseFile -Raw
    if ($javaRelease -match 'JAVA_VERSION="([0-9]+)') { $javaMajor = [int]$Matches[1] }
}
if ($javaMajor -lt 17 -or $javaMajor -ge 25) {
    $javaCandidates = @(
        (Get-ChildItem (Join-Path $env:ProgramFiles 'Microsoft') -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match '^jdk-(17|18|19|20|21|22|23|24)' } |
            Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty FullName),
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
.\gradlew.bat test lint connectedDebugAndroidTest
if ($ManagedDevice) {
    .\gradlew.bat phase0Api35DebugAndroidTest
}
