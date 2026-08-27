param(
    [string]$OutputPath = (Join-Path $PSScriptRoot '..\infra\cloudrun\queue.rendered.yaml'),
    [string]$Queue = $env:PETI_ANALYSIS_QUEUE_NAME,
    [string]$ServiceAccount = $env:PETI_ANALYSIS_TASK_SERVICE_ACCOUNT,
    [string]$Audience = $env:PETI_ANALYSIS_TASK_AUDIENCE
)

$ErrorActionPreference = 'Stop'

function Require-Value([string]$Name, [string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) {
        throw "Missing required configuration input: $Name"
    }
}

Require-Value 'PETI_ANALYSIS_QUEUE_NAME' $Queue
Require-Value 'PETI_ANALYSIS_TASK_SERVICE_ACCOUNT' $ServiceAccount
Require-Value 'PETI_ANALYSIS_TASK_AUDIENCE' $Audience

$templatePath = Join-Path $PSScriptRoot '..\infra\cloudrun\queue.yaml.template'
$template = Get-Content -Raw -LiteralPath $templatePath
$rendered = $template.Replace('${PETI_ANALYSIS_QUEUE_NAME}', $Queue)
    .Replace('${PETI_ANALYSIS_TASK_SERVICE_ACCOUNT}', $ServiceAccount)
    .Replace('${PETI_ANALYSIS_TASK_AUDIENCE}', $Audience)

$resolvedOutput = [IO.Path]::GetFullPath((Join-Path (Get-Location) $OutputPath))
$outputDirectory = Split-Path -Parent $resolvedOutput
New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null
Set-Content -LiteralPath $resolvedOutput -Value $rendered -Encoding utf8NoBOM
Write-Output $resolvedOutput
