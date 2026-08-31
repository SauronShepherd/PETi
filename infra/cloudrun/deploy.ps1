param(
    [ValidateSet("dev", "staging", "production")]
    [string]$Environment = "dev",
    [string]$Region = $env:PETI_TASKS_LOCATION,
    [string]$Project = $env:PETI_PROJECT_ID,
    [string]$Queue = $env:PETI_ANALYSIS_QUEUE_NAME,
    [string]$WorkerServiceAccount = $env:PETI_ANALYSIS_TASK_SERVICE_ACCOUNT,
    [string]$WorkerAudience = $env:PETI_ANALYSIS_TASK_AUDIENCE,
    [string]$MaintenanceServiceAccount = $env:PETI_MAINTENANCE_EXPECTED_SERVICE_ACCOUNT,
    [string]$MaintenanceAudience = $env:PETI_MAINTENANCE_TASK_AUDIENCE,
    [string]$FirebaseProject = $env:PETI_FIREBASE_PROJECT_ID,
    [string]$MediaBucket = $env:PETI_MEDIA_BUCKET,
    [bool]$AiEnabled = $true,
    [bool]$ProviderEnabled = $true,
    [bool]$ModelEnabled = $true
)

$ErrorActionPreference = "Stop"
$apiService = "peti-api-$Environment"
$workerService = "peti-worker-$Environment"
$repository = "peti"
$imagePrefix = "$Region-docker.pkg.dev/$Project/$repository/peti"
$apiImage = "$imagePrefix-api:$Environment"
$workerImage = "$imagePrefix-worker:$Environment"

function Require-Value([string]$Name, [string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) { throw "Missing required deployment value: $Name" }
}

function Invoke-Gcloud([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments) {
    & gcloud @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }
}

Require-Value "PETI_PROJECT_ID" $Project
Require-Value "PETI_TASKS_LOCATION" $Region
Require-Value "PETI_ANALYSIS_QUEUE_NAME" $Queue
Require-Value "PETI_ANALYSIS_TASK_SERVICE_ACCOUNT" $WorkerServiceAccount
Require-Value "PETI_ANALYSIS_TASK_AUDIENCE" $WorkerAudience
Require-Value "PETI_MAINTENANCE_EXPECTED_SERVICE_ACCOUNT" $MaintenanceServiceAccount
Require-Value "PETI_MAINTENANCE_TASK_AUDIENCE" $MaintenanceAudience
Require-Value "PETI_FIREBASE_PROJECT_ID" $FirebaseProject
Require-Value "PETI_MEDIA_BUCKET" $MediaBucket

Invoke-Gcloud config set project $Project | Out-Null
& gcloud artifacts repositories describe $repository --location=$Region --format="value(name)" *> $null
if ($LASTEXITCODE -ne 0) {
    Invoke-Gcloud artifacts repositories create $repository --repository-format=docker --location=$Region --description="PETi sandbox container images"
}
& gcloud tasks queues describe $Queue --location=$Region *> $null
if ($LASTEXITCODE -ne 0) {
    Invoke-Gcloud tasks queues create $Queue --location=$Region --max-attempts=5 --max-concurrent-dispatches=10 --max-dispatches-per-second=2 --task-timeout=300s
}

$envArgs = @(
    "PETI_ENVIRONMENT=$($Environment.ToUpperInvariant())",
    "PETI_AUTH_MODE=FIREBASE",
    "PETI_STORAGE_MODE=FIRESTORE",
    "PETI_PROJECT_ID=$Project",
    "PETI_FIREBASE_PROJECT_ID=$FirebaseProject",
    "PETI_MEDIA_BUCKET=$MediaBucket",
    "PETI_MEDIA_SIGNING_SERVICE_ACCOUNT=$MaintenanceServiceAccount",
    "PETI_TASKS_PROJECT_ID=$Project",
    "PETI_TASKS_LOCATION=$Region",
    "PETI_ANALYSIS_QUEUE_NAME=$Queue",
    "PETI_ANALYSIS_TASK_SERVICE_ACCOUNT=$WorkerServiceAccount",
    "PETI_ANALYSIS_TASK_AUDIENCE=$WorkerAudience",
    "PETI_ANALYSIS_EXPECTED_SERVICE_ACCOUNT=$WorkerServiceAccount",
    "PETI_MAINTENANCE_EXPECTED_SERVICE_ACCOUNT=$MaintenanceServiceAccount",
    "PETI_MAINTENANCE_TASK_AUDIENCE=$MaintenanceAudience",
    "PETI_AI_PROVIDER=GEMINI",
    "PETI_AI_MODEL=gemini-3.5-flash",
    "PETI_AI_ENABLED=$($AiEnabled.ToString().ToLowerInvariant())",
    "PETI_AI_PROVIDER_ENABLED=$($ProviderEnabled.ToString().ToLowerInvariant())",
    "PETI_AI_MODEL_ENABLED=$($ModelEnabled.ToString().ToLowerInvariant())",
    "PETI_GEMINI_TRANSPORT=SDK",
    "PETI_GEMINI_LOCATION=global",
    "PETI_CHECK_ENABLED=false"
    ,"PETI_AGENT_RUNTIME_ENABLED=true"
)

Invoke-Gcloud builds submit . --config=infra/cloudrun/cloudbuild.yaml --substitutions="_ENVIRONMENT=$Environment,_IMAGE_PREFIX=$imagePrefix"
 $workerEnvArgs = ($envArgs + "PETI_SERVICE=peti-worker") -join ","
Invoke-Gcloud run deploy $workerService --image=$workerImage --region=$Region --no-allow-unauthenticated "--set-env-vars=$workerEnvArgs"
$workerUrl = (& gcloud run services describe $workerService --region=$Region --format="value(status.url)").Trim()
if ($LASTEXITCODE -ne 0) { throw "gcloud run services describe worker failed with exit code $LASTEXITCODE" }
if ([string]::IsNullOrWhiteSpace($workerUrl)) { throw "Worker URL was not returned by Cloud Run" }

Invoke-Gcloud run services add-iam-policy-binding $workerService --region=$Region --member="serviceAccount:$WorkerServiceAccount" --role=roles/run.invoker
 $apiEnvArgs = ($envArgs + "PETI_SERVICE=peti-api" + "PETI_ANALYSIS_WORKER_URL=$workerUrl") -join ","
Invoke-Gcloud run deploy $apiService --image=$apiImage --region=$Region --allow-unauthenticated "--set-env-vars=$apiEnvArgs"

Write-Host "Deployed private worker: $workerService ($workerUrl)"
Write-Host "Deployed public API: $apiService"
Write-Host "PETi Check remains disabled until evaluation evidence is approved."
