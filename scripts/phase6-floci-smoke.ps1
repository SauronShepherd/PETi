param(
    [string]$ApiBaseUrl = 'http://127.0.0.1:8000',
    [string]$AccessToken = "local-test:phase6-smoke-$([guid]::NewGuid().ToString('N'))"
)

$ErrorActionPreference = 'Stop'

$headers = @{
    Authorization = "Bearer $AccessToken"
    'Idempotency-Key' = [guid]::NewGuid().ToString()
}

function Invoke-Peti([string]$Method, [string]$Path, $Body = $null, [hashtable]$ExtraHeaders = @{}) {
    $requestHeaders = @{}
    $headers.Keys | ForEach-Object { $requestHeaders[$_] = $headers[$_] }
    $ExtraHeaders.Keys | ForEach-Object { $requestHeaders[$_] = $ExtraHeaders[$_] }
    $params = @{ Method = $Method; Uri = "$ApiBaseUrl$Path"; Headers = $requestHeaders }
    if ($null -ne $Body) {
        $params.Body = ($Body | ConvertTo-Json -Depth 10)
        $params.ContentType = 'application/json'
    }
    Invoke-RestMethod @params
}

$pet = Invoke-Peti POST '/v1/pets' @{ display_name = 'Floci Phase 6'; species = 'DOG' } @{ 'Idempotency-Key' = [guid]::NewGuid().ToString() }
$petId = $pet.id

$measurement = Invoke-Peti POST "/v1/pets/$petId/measurements" @{
    measurement_type = 'WEIGHT'
    original_value = '22.4'
    original_unit = 'lb'
    source_class = 'MEASURED'
} @{ 'Idempotency-Key' = [guid]::NewGuid().ToString() }

$dueAt = (Get-Date).ToUniversalTime().AddHours(-1).ToString('o')
$care = Invoke-Peti POST "/v1/pets/$petId/care" @{
    category = 'CUSTOM'
    title = 'Floci smoke reminder'
    due_at = $dueAt
    repeat_frequency = 'WEEKLY'
    repeat_interval = 1
    notification_enabled = $true
    timezone = 'UTC'
} @{ 'Idempotency-Key' = [guid]::NewGuid().ToString() }

$device = Invoke-Peti POST '/v1/me/devices' @{
    installation_id = "floci-phase6-installation-$([guid]::NewGuid().ToString('N'))"
    fcm_token = 'floci-phase6-token'
    platform = 'ANDROID'
    app_version = 'local-smoke'
    notifications_permission_state = 'GRANTED'
}

$dispatchHeaders = @{
    'X-Task-Service-Identity' = 'floci-cloud-tasks'
    'X-Task-Audience' = 'local'
}
$firstDispatch = Invoke-Peti POST '/v1/internal/tasks/notifications' $null $dispatchHeaders
$secondDispatch = Invoke-Peti POST '/v1/internal/tasks/notifications' $null $dispatchHeaders
$inbox = Invoke-Peti GET '/v1/internal/local/notifications/inbox'

if ($firstDispatch.deliveries.Count -ne 1) { throw 'Expected one local FCM delivery.' }
if ($secondDispatch.deliveries.Count -ne 0) { throw 'Expected delivery deduplication.' }
if ($inbox.inbox.Count -ne 1) { throw 'Expected one message in the local FCM inbox.' }

Invoke-Peti PATCH '/v1/me/notification-preferences' @{ care_notifications_enabled = $false } | Out-Null
$careState = Invoke-Peti GET "/v1/pets/$petId/care"
$occurrences = Invoke-Peti GET "/v1/pets/$petId/care-occurrences"
$timeline = Invoke-Peti GET "/v1/pets/$petId/timeline"

[pscustomobject]@{
    pet_id = $petId
    measurement_id = $measurement.id
    care_id = $care.id
    device_id = $device.id
    normalized_weight_kg = $measurement.normalized_value
    first_dispatch_count = $firstDispatch.deliveries.Count
    second_dispatch_count = $secondDispatch.deliveries.Count
    inbox_count = $inbox.inbox.Count
    care_count_after_notification_disable = $careState.Count
    occurrence_count_after_notification_disable = $occurrences.Count
    timeline_count = $timeline.Count
}
