[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z][a-z0-9-]{4,28}[a-z0-9]$')]
    [string]$ProjectId,

    [ValidateSet('DEV', 'STAGING')]
    [string]$Environment = 'DEV',

    [string]$Region = 'europe-west1'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Invoke-GcloudJson([string[]]$Arguments) {
    $json = & gcloud @Arguments --format=json --quiet
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud command failed: gcloud $($Arguments -join ' ')"
    }
    if ([string]::IsNullOrWhiteSpace(($json -join ''))) {
        return $null
    }
    return ($json -join "`n") | ConvertFrom-Json
}

if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    throw 'gcloud CLI is required.'
}

$active = Invoke-GcloudJson @('auth', 'list', '--filter=status:ACTIVE')
if (-not $active -or @($active).Count -eq 0) {
    throw 'No active gcloud account is configured. Run gcloud auth login first.'
}

$project = Invoke-GcloudJson @('projects', 'describe', $ProjectId)
if (-not $project -or $project.lifecycleState -ne 'ACTIVE') {
    throw "Project '$ProjectId' is not active."
}

$billing = Invoke-GcloudJson @('billing', 'projects', 'describe', $ProjectId)
$services = Invoke-GcloudJson @('services', 'list', '--project', $ProjectId, '--enabled')
$account = @($active)[0].account
$iam = Invoke-GcloudJson @('projects', 'get-iam-policy', $ProjectId, '--flatten=bindings[].members', "--filter=bindings.members:$account")

[ordered]@{
    mode = 'READ_ONLY'
    project_id = $project.projectId
    project_number = $project.projectNumber
    environment = $Environment
    region = $Region
    billing_enabled = [bool]$billing.billingEnabled
    billing_account = $billing.billingAccountName
    enabled_services = @($services | ForEach-Object { $_.config.name } | Sort-Object)
    iam_policy_roles = @($iam.bindings | ForEach-Object { $_.role } | Sort-Object -Unique)
    iam_permission_probe = 'NOT_AVAILABLE_IN_GCLOUD_SURFACE'
    mutation_performed = $false
    customer_data_accessed = $false
    real_gemini_called = $false
} | ConvertTo-Json -Depth 5
