param(
    [Parameter(Mandatory = $true)][string]$ProjectId,
    [Parameter(Mandatory = $true)][string]$AppId
)

$ErrorActionPreference = "Stop"
$outputPath = Join-Path $PSScriptRoot "..\android\app\google-services.json"
$token = (gcloud auth print-access-token)
if (-not $token) { throw "gcloud user authentication is required." }
$headers = @{ Authorization = "Bearer $token"; 'x-goog-user-project' = $ProjectId }
$uri = "https://firebase.googleapis.com/v1beta1/projects/$ProjectId/androidApps/$AppId/config"
$response = Invoke-RestMethod -Uri $uri -Headers $headers -Method Get
$bytes = [Convert]::FromBase64String($response.configFileContents)
[IO.File]::WriteAllBytes((Resolve-Path (Join-Path $PSScriptRoot "..\android\app")).Path + "\google-services.json", $bytes)
Write-Output "Firebase Android configuration written to android/app/google-services.json (ignored by git)."
