param(
    [string]$ProjectId = "demo-peti"
)

$ErrorActionPreference = "Stop"
$firebaseEntryPoint = Join-Path $env:APPDATA "npm\node_modules\firebase-tools\lib\bin\firebase.js"

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw "Node.js is required to run the Firebase emulator matrix."
}
if (-not (Test-Path -LiteralPath $firebaseEntryPoint)) {
    throw "Firebase CLI entry point was not found at $firebaseEntryPoint. Install firebase-tools first."
}

$env:CI = "1"
$env:JAVA_TOOL_OPTIONS = "-Djdk.net.unixdomain.tmpdir=C:\Temp\peti-java-sockets"

& node $firebaseEntryPoint emulators:exec `
    --only auth,firestore,storage `
    --project $ProjectId `
    "node scripts/firebase-emulator-probe.js"

if ($LASTEXITCODE -ne 0) {
    throw "Firebase emulator matrix failed with exit code $LASTEXITCODE."
}
