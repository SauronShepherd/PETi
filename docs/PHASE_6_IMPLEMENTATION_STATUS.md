# Phase 6 implementation status

This document maps the Phase 6 build plan to current workspace evidence.

## Proven locally

- Measurements: deterministic kg/lb and °C/°F conversion with high-precision
  normalized storage, original source value/unit preservation, explicit
  provenance, client rejection of `AI_ESTIMATED`, conflicts coexist,
  idempotent create, locale-safe decimal entry, measured-only filtering,
  explicit AI-estimate opt-in, deterministic chronological trend deltas, and
  owner scoping.
- Timeline: bounded `All`, `Checks`, `Measurements`, and `Care` filters,
  deterministic ordering, measurement/Care projections, and completed PETi
  Check projections linked to canonical result IDs.
- List queries: measurements, Care plans, and occurrences are ordered by
  canonical timestamps with stable ID tie-breakers rather than insertion order.
- Care: create/list/detail/update/delete, explicit categories/timezones,
  persistent occurrences with completion/skip/reschedule history, recurring
  once/daily/weekly/monthly/custom-interval next-occurrence generation for
  completion and skip, timezone validation with local-wall-clock recurrence,
  action idempotency, and
  recurrence-safe edits that preserve historical records.
- Notifications: preference/device records, permission-independent Care state,
  permission-state-aware device registration, due dispatch deduplication,
  quiet-hours suppression in the configured timezone, minimal payload, and
  account-scoped deep-link resolution.
- Deployment boundary: task-authenticated notification dispatch with a lazy
  Firebase Admin FCM sender in non-LOCAL environments; LOCAL uses only the
  fake FCM inbox endpoints.
- Delivery failures: invalid/unregistered provider tokens are recorded as
  `FAILED_FINAL`; other provider failures remain `FAILED_RETRYABLE`, and no
  failure path mutates or deletes the Care occurrence.
- Cloud state: Firestore writes and process-restart hydration for Phase 6
  records.
- Firestore deployment metadata: composite indexes for measurement history,
  Care occurrence queries, and notification deduplication.
- Observability: safe Timeline, measurement, Care, notification permission,
  and delivery events through the existing allow-listed analytics recorder;
  exact values, notes, narratives, and FCM tokens are excluded.
- Android: Phase 6 panel, authenticated API boundary, manual-only temperature
  copy, explicit measured/documented/reported provenance entry, measured-only
  filtering, notification permission UX, FCM token registration, notification
  rendering, opaque Care deep links, and complete/skip/reschedule occurrence
  actions with idempotency keys.
- Runtime evidence: manual API-35 AVD instrumentation 5/5 passed through
  `scripts/run-android-tests-manual.ps1` with SwiftShader when the Gradle
  managed-device snapshot was unavailable.
- Android reads: disposable user-scoped cache for Timeline, measurements,
  trends, Care, occurrences, and notification preferences; successful writes
  invalidate related projections and cache misses never fabricate data.
- Deep-link resolution uses exact occurrence-ID matching against the
  authenticated occurrence response before presenting the target as opened.
- Android Care presentation: explicit accessible status labels for upcoming,
  due, overdue, completed, skipped, and canceled occurrences.
- Android Care creation: recurrence choices for once, daily, weekly, and
  monthly schedules, category selection, optional notes, and notification
  preference state carried into the created Care item.

## Current local evidence

The current workspace has now been verified with:

```text
backend: 120 tests passed
backend: ruff clean
backend: mypy clean
android: debug unit tests passed
android: debug lint passed
android: release build with R8 passed
android: manual API-35 AndroidX instrumentation passed (5/5) through
`scripts/run-android-tests-manual.ps1` with SwiftShader
local Phase 6 API smoke passed: measurement, Care, device registration,
deduplicated notification dispatch, local inbox, preferences, occurrences,
and Timeline
local Phase 6 API smoke passed with `PETI_STORAGE_MODE=FIRESTORE_EMULATOR`
against the healthy Floci container (`peti-floci-gcp`)
```

## Requires DEV/device infrastructure

- Real Firebase/Firestore restart and account-switch verification.
- Real FCM delivery, permission-denied behavior, notification tap, and
  wrong-account deep-link verification.
- Emulator/physical-device process death, reinstall, accessibility, locale,
  DST/timezone, and rendered conversion review.
- Production scheduler/task wiring and provider failure telemetry.

Phase 6 must not be marked as fully exited until the second section is
completed with recorded evidence.
## Local FCM emulation

When `PETI_ENVIRONMENT=LOCAL`, the internal endpoints below emulate the
notification transport without contacting Firebase:

- `POST /v1/internal/local/notifications/dispatch` runs the normal due-item
  dispatcher against the local FCM sender.
- `GET /v1/internal/local/notifications/inbox` exposes message IDs and opaque
  occurrence IDs captured by that sender.

These endpoints are unavailable outside `LOCAL`. They preserve the normal
rules for disabled care, disabled preferences, denied permission, and duplicate
occurrence/device deliveries. This is local behavioral emulation, not proof of
real FCM or Android OS delivery.

Debug and internal Android variants also use an in-memory `LocalPhase6Repository`
so measurement, Care, occurrence, preference, and device flows remain visible
within a local app session. Release builds continue to use the authenticated
API repository.

The repeatable local harness is
`scripts/phase6-floci-smoke.ps1`. It is designed to run against the API started
by `scripts/run-local-emulator.ps1` and exercises the complete local Floci plus
fake-FCM path without contacting Firebase. The latest run passed against the
local API using the in-memory adapters and was then repeated against the Floci
Firestore emulator successfully. The Firestore adapter queries now use the
named `FieldFilter` API; the latest emulator run was clean.

The route and payload reference is [PHASE_6_API.md](PHASE_6_API.md).
