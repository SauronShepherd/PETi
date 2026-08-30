$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$webPort = 4173
$listener = Get-NetTCPConnection -LocalPort $webPort -ErrorAction SilentlyContinue | Select-Object -First 1
if ($listener) {
  Write-Host "PETi web ya está disponible en http://localhost:$webPort/?demo=1"
  Start-Process "http://localhost:$webPort/?demo=1"
  exit 0
}
Write-Host "Sirviendo PETi web en http://localhost:$webPort/?demo=1"
Write-Host "Pulsa Ctrl+C para detener el servidor."
Push-Location $projectRoot
try { python -m http.server $webPort --bind 0.0.0.0 -d web }
finally { Pop-Location }
