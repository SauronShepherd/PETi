# PETi — Google Play App Signing Configuration

Status: `PENDING_EXTERNAL_GOOGLE_PLAY_ACCOUNT`

This document defines the release configuration without storing signing keys,
service-account credentials, or Play Console secrets in the repository.

## Required Play Console configuration

1. Create or select the application package `com.peti.app`.
2. Enrol the application in Google Play App Signing.
3. Generate the upload key locally in a protected operator environment.
4. Export only the upload certificate (`.der`/SHA-256 fingerprint) for Play
   Console registration. Never commit the private upload key.
5. Configure the Play App Signing app-signing key and upload key separately.
6. Create the Premium subscription and base plan required by the billing
   contract, then record its product identifier in the production secret
   manager, not in source.

## Repository release contract

- `android/app/build.gradle.kts` must receive signing values from the release
  environment; no passwords or private keys are accepted from source files.
- `scripts/inspect_release_artifact.py` must inspect the produced signed AAB
  before submission.
- `release/EXTERNAL_GATES.md` must link the Play product, license-tester
  lifecycle, signed-AAB inspection, and rollback evidence before a GO decision.
- Upload-key recovery follows `docs/runbooks/UPLOAD_KEY_RECOVERY.md`.

## Evidence required before Phase 17 is green

- Play App Signing enrolment confirmation.
- Upload certificate fingerprint and protected key custody record.
- Signed production AAB with matching package and certificate metadata.
- License-tester purchase, renewal, grace, hold, recovery, and cancellation
  evidence.
- Play Console declarations and review submission record.

No external account or credential is implied by this source document.
