# All detailed build plans — implementation status

The canonical source directory is:

`C:\ANGEL\Personal\Hackathons\20260817 - Gemini - PETI`

This workspace implementation now includes the Phase 0–7 foundations plus the
following later-domain implementation tranches:

- Phases 8–11: dog-only specialist analysis types, provenance, guardrails,
  Initial Scan candidates/review, Dental/Feces/Body APIs, and Body comparison.
- Phase 12: deterministic Weekly PETi Reports with immutable source references.
- Phase 13: backend-authoritative Premium entitlement reconciliation boundary.
- Phase 14: account export and deletion orchestration.
- Out-of-scope modules: export/share/import objects, caregiver invitations and
  memberships, deterministic automation rules, scoped search/memory,
  source-grounded assistant threads, and Android access surfaces are present as
  research scaffolding. They are not phases of the approved 0–17 plan and must
  not be treated as certified product scope; their runtime exposure remains an
  explicit scope/security gap in `PETI_GAP_ANALYSIS_BUILD_PLAN.md`.
- Phase 15–17 operational work: operational metrics, support codes/cases,
  administrative feature flags, emergency cost controls, and release/privacy
  readiness documentation are tracked under the canonical Phase 15–17 plans;
  no invented phase numbers are used here.

The following local verification is currently green:

- Backend: 255 pytest tests, Ruff, mypy, architecture/secret inspection, and
  Phase 1 security inspection.
- Local/Floci acceptance: Phase 4/5 acceptance bundle, red-team checks,
  metadata smoke, fake PETi Check, and delivery/deduplication/inbox/timeline
  smoke.
- Android: debug unit tests, lint, debug/internal/release builds including R8,
  and manual API-35 AndroidX instrumentation with 5/5 tests passed using the
  SwiftShader emulator runner.

The Gradle-managed API-35 device remains unreliable in this environment because
its snapshot/process crashes before instrumentation starts; the manual ADB
runner is the reproducible local fallback and does not use GCP.

The remaining gates are intentionally not represented as passed merely because
their API or domain skeleton exists. They require real Firebase Auth/Firestore/
Storage/FCM, Cloud Tasks/IAM/Cloud Run deployment, production Gemini/OCR/VLM/
ADK evaluation, Google Play/email delivery, or physical-device validation.

