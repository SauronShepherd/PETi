# PETi Phases 0–17 — Continuation Status

Updated: 2026-08-26

This status supplements the historical gap analysis. It records changes made
after that audit and does not claim external certification from local tests.

## Local implementation completed in this continuation

- Phase 2: concurrent credit reservation coverage, concurrent Premium
  reconciliation coverage, named fake reward verifier, and AdMob initialization
  confined to the funding flow.
- Phase 3: media status state machine, authoritative GCS checksum path,
  abandoned-upload cleanup, unique WorkManager retry names, and Android build
  verification.
- Phase 4: exclusive analysis-job claims, provider error taxonomy, file-backed
  prompt/schema registry, provider-independent safety merge and kill-switch
  coverage.
- Phase 5: canonical `GOOD/PARTIAL/INSUFFICIENT` evidence quality, excessive
  certainty guardrail, server-controlled possible-interpretations flag, and
  PETi Check safety regression coverage.
- Phases 7–8: document-measurement FK cascade coverage and Initial Scan
  provenance states (`AI_SUGGESTED`, `USER_CONFIRMED`, `USER_CORRECTED`).
- Phase 12: timezone-aware report keys and distinct change states
  (`MEANINGFUL_CHANGE`, `NO_MEANINGFUL_CHANGE`, `NOT_ENOUGH_DATA`).
- Phase 14: FCM/device-token cleanup, identity tombstones, explicit deletion
  dependency graph, and independently queryable residual verification.
- Phase 17: Play App Signing configuration, expanded Play worksheets,
  reviewer instructions, and fail-closed submission record.
- Phase 2: funding gateway moved into the dedicated `:features:funding` Gradle
  module; the app retains only the funding UI/repository integration.
- Phase 3: CameraX 1.4.1 dependencies, embedded `PreviewView` capture, and
  `CameraXCaptureController` photo/video output are wired into the PETi Check
  capture buttons. Physical camera behavior remains an external device gate.
- Phase 3: microphone capture now has an explicit runtime permission flow,
  FileProvider-backed `cache/audio` URIs, durable upload metadata, and audio
  type preservation through PETi Check submission. Physical microphone QA
  remains external.
- Phase 13: Android Play Billing 7.1.1 client boundary now supports product
  discovery, purchase callbacks, restore, and server-only reconciliation via
  `PremiumReconciliationPort`. Release services use the authenticated API
  reconciliation adapter; debug/internal services reject local entitlement
  grants. Real Play product/license-tester execution is still external.
- Phase 13 backend: Premium reconciliation now has explicit local coverage for
  ACTIVE, GRACE, HOLD, CANCELED-entitled, EXPIRED, and REVOKED states, plus
  cross-account purchase-token replay rejection.
- Phase 14: account deletion now installs an independent
  `MediaStorageResidualInventory` when Firestore media metadata and object
  storage adapters are present. It probes canonical objects directly, so
  caller-provided residual counts cannot falsely pass the media gate.
- Phase 16: added `AccessibilityRegressionTest` covering primary-button
  operability and editable pet creation semantics; TalkBack and physical
  device accessibility review remain external.
- Phase 16 CI: artifact inspection now scans APK/AAB payload bytes as well as
  entry names and is wired to the generated debug APK in the GitHub workflow;
  production mode still rejects debug-only markers.
- Phase 16 Android persistence: `AccountSwitchPersistenceTest` now covers
  selected-pet isolation between users and session survival through activity
  recreation. True process death, uninstall/reinstall, and physical-device
  execution remain external gates.
- Privacy: queued-work tombstone gate and specialist certificate fail-closed
  release validation are now covered locally.
- Phase 17: added `check_play_worksheets.py`, wired into local checks and CI,
  to ensure the five Play compliance/reviewer documents remain populated and
  scope-consistent. Submission, legal approval and Play Console evidence remain
  external.
- CI release handling: GitHub Actions always gates debug/tests/lint and runs
  `assembleRelease` only when both production AdMob secrets are present;
  otherwise it reports the external release-input gate explicitly.
- Phase 15–17: kill-switch flags hydrate/persist through
  `FirestoreFeatureFlagStore` when Firestore is configured; non-LOCAL routes
  for out-of-scope research surfaces are fail-closed, while LOCAL remains the
  explicit fixture environment.
- Scope enforcement: `scripts/check_scope_guard.py` is part of the root quality
  gate and verifies the fail-closed middleware markers and experimental-route
  boundary remain present.
- Phase 0 infrastructure: the sandbox Terraform root now passes formatting,
  initialization, and validation; the API receives the worker OIDC audience
  explicitly (`PETI_ANALYSIS_TASK_AUDIENCE`). Apply/IAM/runtime verification
  remains an external GCP gate. The same sandbox checks are now part of
  `scripts/check.ps1`.
- Phase 3 infrastructure: Terraform now declares an hourly Cloud Scheduler
  job for `/v1/internal/tasks/media-maintenance`, with a dedicated API runtime
  OIDC identity/audience (`peti-maintenance-<environment>`) and Cloud Run
  invocation IAM. An authenticated plan reports 40 resources to add and no
  changes/destroys; apply and live sweep execution remain external GCP gates.

## Current local evidence

- Backend suite: 255 tests collected; the latest full gate completed with all tests passing.
- Ruff, Mypy, architecture/secret checks, billing security and release-manifest
  checks pass.
- Android Gradle verification now passes with the documented Windows JVM
  loopback workaround: `testDebugUnitTest`, `testInternalUnitTest`,
  `testReleaseUnitTest`, `lint`, and `assembleDebug` complete successfully.
  The funding module declares the `internal` variant and its INTERNET
  permission; the workaround is recorded in
  `docs/runbooks/ANDROID_BUILD_ENVIRONMENT.md`.
- Release status remains `PASS_STATIC_ONLY`.

## External gates intentionally still pending

- Full authenticated product runtime smoke against the applied GCP sandbox.
  The Scheduler OIDC path, real Gemini PETi Check evaluation, generic agent
  execution, and specialist worker persistence slices have passed; customer
  authentication, upload/media, and full product-domain smoke remain pending.
- Real Gemini PETi Check held-out/red-team execution has passed for the
  evaluated sandbox configuration. Specialist red-team smoke has executed and
  passed schema/guardrail checks, but full held-out/regression certification
  and independent certificates remain pending.
- Real FCM delivery and notification/device evidence.
- Google Play product, RTDN, license-tester lifecycle, Play App Signing and
  signed production AAB evidence.
- Physical-device accessibility, process-death/reinstall/account-switch
  evidence and Play review.
- Public HTTPS publication and legal approval of privacy/deletion resources.
- Production telemetry, SLO, cost and rollback drills.

These gates require external accounts, credentials, devices or deployed
infrastructure and must not be inferred from source-level or local evidence.

