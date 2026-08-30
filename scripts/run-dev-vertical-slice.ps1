$ErrorActionPreference='Stop'

if (-not $env:PETI_AUTH_MODE -or $env:PETI_AUTH_MODE -ne 'FIREBASE') { throw 'Set PETI_AUTH_MODE=FIREBASE for the DEV vertical slice.' }
if (-not $env:PETI_FIREBASE_PROJECT_ID) { throw 'Set PETI_FIREBASE_PROJECT_ID; credentials must come from ADC/IAM.' }
if (-not $env:GOOGLE_APPLICATION_CREDENTIALS -and -not $env:GCLOUD_PROJECT) { throw 'Configure ADC or GCLOUD_PROJECT; never commit service-account JSON.' }
Write-Output 'DEV vertical slice prerequisites are present. Use the reviewed web deployment path.'
