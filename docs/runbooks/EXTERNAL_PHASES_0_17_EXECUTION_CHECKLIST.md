# PETi Phases 0–17 — External Execution Checklist

This runbook is the hand-off for gates that cannot be proven by the repository
alone. Execute it against the frozen release revision and attach immutable
outputs to the release evidence manifest. Never replace a `PENDING` value with
`PASS` without the corresponding artifact.

## 1. Sandbox GCP smoke

Use only the non-production project and region recorded in `release/EXTERNAL_GATES.md`.

1. Confirm the API and worker revisions are `Ready`, the analysis queue is
   `RUNNING`, the maintenance Scheduler is `ENABLED`, and the application
   bucket is private.
2. Execute the Scheduler OIDC maintenance job and retain the execution result,
   request correlation ID, Cloud Run revision, and response status.
3. Create one disposable owner-scoped fixture and run the full vertical slice:
   authenticated sign-in → pet → media → analysis/task → result → deletion.
4. Capture Firestore and GCS residual inventories after deletion. The expected
   result is zero owner-scoped documents and zero canonical objects.

Required artifacts: command output, Cloud Run logs, Firestore inventory,
GCS inventory, Terraform revision, and a redacted evidence manifest.

## 2. Provider and billing gates

- Gemini: execute each `dev`, `held_out`, `red_team`, and `regression` manifest
  against the exact provider/model/config; retain request IDs, model ID, prompt
  and guardrail versions, cost, hard-gate metrics, and raw red-team outcomes.
- Google Play: create the product/base plan, run the license-tester lifecycle,
  verify canonical `subscriptionsv2` reads, deliver authenticated RTDN, and
  retain Play Console and Pub/Sub evidence.
- AdMob/SSV: use official test ads and retain the signed callback and replay
  result.

## 3. Device and release gates

Run the matrix on low-resource, mainstream, and recent physical devices:

- sign-in, account switch, reinstall and process death;
- CameraX, Photo Picker, SAF PDF, microphone, notifications and deep links;
- measurements, care, records, reports, specialists and billing;
- TalkBack, large text, touch targets, non-color state and rotation.

Build the signed AAB only after production signing and Play App Signing are
configured. Inspect the final artifact for API keys, service-account files,
local AI/provider code, debug bypasses and out-of-scope routes.

## 4. Evidence and stop conditions

For every run record: frozen revision, environment, actor, timestamp, command
or test ID, result, artifact path/hash, and any cleanup performed. Stop and
leave the gate pending when credentials, product configuration, legal text,
device access, or provider quota is missing. Do not infer production readiness
from local fakes, source manifests, Cloud Run liveness, or a successful static
release gate.
