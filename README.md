# PETi

PETi is a cloud-only AI companion for pet care. Phase 0 is the engineering foundation: a native Android shell, a typed FastAPI service, shared contracts, deterministic fakes, and automated architecture gates.

## Quick start

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e backend[dev]
./scripts/check
./scripts/run-backend
```

On Windows, use `scripts\bootstrap.cmd`, `scripts\check.cmd`, and `scripts\run-backend.ps1`.

The local backend exposes `GET /health/live` and `GET /health/ready`. No production credentials or paid AI services are required.

See [docs/ARCHITECTURE_INVARIANTS.md](docs/ARCHITECTURE_INVARIANTS.md), [docs/PHASE_0.md](docs/PHASE_0.md), and [docs/PHASE_1.md](docs/PHASE_1.md).

Phase 1 local verification uses explicit `local-test:<identity>` credentials. For a local cloud-shaped persistence layer, start Floci with `scripts\start-local-emulator.ps1`; it runs Firestore locally in Docker and requires no GCP account, ADC, IAM, or billing. The real DEV path remains fail-closed behind `PETI_AUTH_MODE=FIREBASE`, and is intentionally deferred.

Run the local Phase 1 persistence smoke test with `scripts\test-floci.ps1`.
# PETi

PETi is a privacy-first pet-care application. Phase 0 and Phase 1 establish authenticated ownership-scoped pet flows. Phase 2 adds the server-authoritative funding control plane for future variable-cost cloud operations.

Phase 6 adds the non-AI longitudinal care foundation: Timeline projections,
measurements with provenance and deterministic conversion, recurring Care and
occurrences, notification preferences, and FCM delivery. Local acceptance can
be exercised against Floci with the documented
`scripts/phase6-floci-smoke.ps1` harness; production notification delivery is
task-authenticated and Firebase-backed.

Phase 7 Floci acceptance is reproducible with
`scripts\test-floci-phase7.ps1`; it starts the local emulator and runs the
Record Vault API E2E without cloud credentials or billing.

Advertising is not a general PETi monetization surface. It is a user-selected funding mechanism offered only when an explicitly requested costly cloud operation lacks sufficient credits. Android never writes economic state directly.

Phase 7 adds the private Veterinary Record Vault. Records reuse the Phase-3
media pipeline, optional document extraction creates reviewable candidates only,
and Confirm/Correct/Reject creates source-traceable `DOCUMENTED` facts.

The all-phase implementation status is tracked in
[docs/ALL_PHASES_IMPLEMENTATION_STATUS.md](docs/ALL_PHASES_IMPLEMENTATION_STATUS.md).

## Hackathon submission materials

PETi is presented in the **Taskmaster** category. The judge-facing architecture,
four-minute demo script, testing instructions, and eligibility/code disclosure
are maintained in [docs/HACKATHON_ARCHITECTURE.md](docs/HACKATHON_ARCHITECTURE.md),
[docs/HACKATHON_DEMO_SCRIPT.md](docs/HACKATHON_DEMO_SCRIPT.md),
[docs/HACKATHON_TESTING_INSTRUCTIONS.md](docs/HACKATHON_TESTING_INSTRUCTIONS.md),
and [docs/CODE_DISCLOSURE.md](docs/CODE_DISCLOSURE.md).

The phase-by-phase implementation audit, evidence references, and remaining
external blockers are recorded in
[release/COMPLETION_AUDIT.md](release/COMPLETION_AUDIT.md).

The current release is free: Play Billing is intentionally not part of the
submission. Real Gemini, production cloud, signed-artifact, physical-device,
public-HTTPS, and Play-console gates are tracked explicitly under `release/`.

Before human validation, run `pwsh -NoProfile -File
scripts/pre-human-validation.ps1`. This regenerates and validates release
evidence, checks security/privacy/scope controls, and inspects the internal
AAB without claiming physical-device, legal, or live authenticated-cloud
qualification.

## Local verification

```text
python -m ruff check backend
python -m pytest --collect-only -q
python -m pytest backend/tests -q
```

The collection-only step is intentional: import and packaging regressions must
fail before the full suite is interpreted as a valid qualification result.

The Android build additionally requires an installed Android SDK and `android/local.properties` or `ANDROID_HOME`, plus a supported JDK (17–24 for the pinned Android Gradle Plugin). `scripts\check.ps1` automatically selects an installed compatible Microsoft JDK when the host default is unsupported; Java 25 is not compatible with the pinned lint toolchain.

When the Gradle managed-device snapshot is unavailable, run the Android
instrumentation directly against an online local AVD (SwiftShader is supported):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run-android-tests-manual.ps1 -StartEmulator
```

This installs the debug APKs and runs the AndroidX suite with `adb`; it never
contacts GCP or paid providers.
