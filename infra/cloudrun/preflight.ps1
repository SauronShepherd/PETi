$ErrorActionPreference = "Stop"
$missing = [System.Collections.Generic.List[string]]::new()

if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) { $missing.Add("gcloud CLI") }
if (-not $env:PETI_PROJECT_ID) { $missing.Add("PETI_PROJECT_ID") }
if (-not $env:PETI_TASKS_LOCATION) { $missing.Add("PETI_TASKS_LOCATION") }
if (-not $env:PETI_ANALYSIS_QUEUE_NAME) { $missing.Add("PETI_ANALYSIS_QUEUE_NAME") }
if (-not $env:PETI_ANALYSIS_TASK_SERVICE_ACCOUNT) { $missing.Add("PETI_ANALYSIS_TASK_SERVICE_ACCOUNT") }
if (-not $env:PETI_ANALYSIS_TASK_AUDIENCE) { $missing.Add("PETI_ANALYSIS_TASK_AUDIENCE") }
if (-not $env:PETI_MAINTENANCE_EXPECTED_SERVICE_ACCOUNT) { $missing.Add("PETI_MAINTENANCE_EXPECTED_SERVICE_ACCOUNT") }
if (-not $env:PETI_MAINTENANCE_TASK_AUDIENCE) { $missing.Add("PETI_MAINTENANCE_TASK_AUDIENCE") }
if (-not $env:PETI_FIREBASE_PROJECT_ID) { $missing.Add("PETI_FIREBASE_PROJECT_ID") }
if (-not $env:PETI_MEDIA_BUCKET) { $missing.Add("PETI_MEDIA_BUCKET") }

$hasCredentialFile = $false
if ($env:GOOGLE_APPLICATION_CREDENTIALS) {
    $hasCredentialFile = Test-Path -LiteralPath $env:GOOGLE_APPLICATION_CREDENTIALS -PathType Leaf
}
$hasActiveGcloudAccount = $false
if (Get-Command gcloud -ErrorAction SilentlyContinue) {
    try {
        $activeAccount = (& gcloud auth list --filter="status:ACTIVE" --format="value(account)" 2>$null | Select-Object -First 1)
        $hasActiveGcloudAccount = -not [string]::IsNullOrWhiteSpace($activeAccount)
    } catch {
        $hasActiveGcloudAccount = $false
    }
}
if (-not $hasCredentialFile -and -not $hasActiveGcloudAccount) {
    $missing.Add("ADC or gcloud authenticated account")
}

if ($missing.Count) {
    Write-Output ("CLOUD_PREFLIGHT_NOT_READY: " + ($missing -join ", "))
    exit 1
}
Write-Output "CLOUD_PREFLIGHT_READY"
