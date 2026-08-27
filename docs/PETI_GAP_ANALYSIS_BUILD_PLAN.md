# PETi — Comprehensive Build Plan: Pending, Incomplete & Wrongly Implemented Work

**Date:** 2026-08-27
**Method:** Six independent research audits of the actual codebase at `C:\Users\angel.alvarez\IdeaProjects\PETi`, cross-checked line-by-line against the canonical 18-phase build plan (Phase 0–17). Every finding below cites `file:line` evidence from the real repository — not from the project's own self-reported status docs, which were found to be materially stale/optimistic in several places (see Finding #1).

**Status legend:** `[x]` confirmed done · `[ ]` gap (with STATUS tag: NOT IMPLEMENTED / PARTIALLY IMPLEMENTED / WRONGLY IMPLEMENTED) · 🔴 = safety-critical or security-critical.

---

## Executive Summary

The repository is **far along in raw volume** (18 backend domains, ~55+ pytest files, hundreds of Android/backend source files) but still has **external certification gaps** in the areas that matter most for a health-adjacent, monetized, cloud AI product: provider execution, billing lifecycle, specialist evidence, and device/runtime validation. It also contains substantial functionality outside the approved 18-phase plan; that scope is now fail-closed outside LOCAL and excluded from the Data Safety worksheet.

### Top 10 critical findings (fix before anything else)

1. **The local backend/architecture checks are currently green** — the latest independent run reports 451 backend tests, Ruff, Mypy, architecture checks, Android Gradle, Android tests/lint/build, and local evaluation gates passing. Sandbox Terraform also passes initialization/validation; GCP apply, IAM, and runtime execution remain external. → [Phase 0](#phase-0)
2. ✅ **Premium billing entitlement is fail-closed locally.** Non-LOCAL startup leaves the verifier unset and `PremiumService` rejects client-supplied trust flags; configured package names are now required exactly. The remaining gap is external: wire and exercise the real Google Play Publisher verifier before production. → [Phase 13](#phase-13)
3. ✅ **RTDN is a trigger for canonical re-fetch.** `PremiumService.reconcile_rtdn` requires an injected canonical verifier and rejects missing/mismatched owner state. The remaining gap is external execution against real Pub/Sub/Google Play delivery. → [Phase 13](#phase-13)
4. 🔴 **Dental Check's runtime release is fail-closed until its certificate is promoted.** Dental output passes `_guardrail_result()` and natural-language forbidden variants are tested; real provider/device red-team evidence remains external. → [Phase 9](#phase-9)
5. 🔴 **PETi Check safety now uses the canonical vocabulary and maximum-severity merge.** Deterministic urgent signals cannot be downgraded by model output; integration and precedence tests cover the invariant. → [Phase 4](#phase-4), [Phase 5](#phase-5)
6. 🔴 **~1,130 LOC / ~half the API surface is outside the canonical 0–17 release scope**, still registered in the application (`future/`, `agents/`, `assistant/`, `automation/`, `care_advanced/`, `collaboration/`, `portability/`, `search/`) and fail-closed outside LOCAL. These extensions now have substantial local contract/regression coverage, but they are not externally certified or declared as shipped functionality; the release worksheet correctly excludes them. → [Scope Creep Audit](#scope-creep--out-of-spec-audit)
7. **Media checksum verification has a production adapter** — `GcsObjectStorage.checksum_object()` downloads canonical bytes and computes SHA-256; the remaining gate is real GCS execution.
8. **Analysis job claiming is guarded locally and transactionally in Firestore** — claimable states are atomically marked `PREPARING_MEDIA`; duplicate-claim tests pass. Real multi-instance Firestore contention remains external.
9. ✅ **Prompt/schema immutability is now source-file-backed.** `backend/app/ai/registry.py` loads the versioned `.md`/`.json` artifacts from disk, hashes them, and activates only registered versions; `test_prompt_registry_files.py` verifies the active content matches those files. Provider execution and frozen-release evidence remain external gates.
10. **Android now has embedded CameraX photo/video capture and a Play Billing gateway/restore path**; full purchase/RTDN/license-tester lifecycle execution remains an external Play gate.

### Cross-cutting observations
- **Evidence debt is concentrated exactly where risk is highest.** Local tests cover Body Check, Weekly Reports, Premium/Billing, Privacy/Deletion, and the extended Future/agent/assistant/automation/collaboration/portability/search/care domains, but real provider, multi-instance, Play lifecycle, and device evidence remains absent. The extended modules still lack external release certification.
- **Guardrail term lists are inconsistently authored.** Two different bug classes recur: (a) underscored/token-style forbidden phrases that can't match natural-language model output (Dental), and (b) partial word-stem coverage that misses common variants (`"dehydrated"` doesn't match `"dehydration"` in Feces; `"bone_loss"`/`"pocket_depth"` never match spaced prose in Dental).
- **Eval/red-team manifests exist and local harnesses execute the available deterministic checks.** Specialist release certificates intentionally remain `PENDING_EXTERNAL_GEMINI` until real provider/device evidence; this is a release gate, not a missing artifact.
- **What genuinely cannot be closed without real external infrastructure** (a live Google Cloud project, Play Console, production Firebase): Phase 13's real Google Play Developer API exercise, Phase 14's true GCS/Firestore residual-zero verification, Phase 15's live SLO/incident drills, Phase 16/17's device-farm and Play submission steps. Everything else below is fixable in this repository today.

---

## Table of Contents
1. [Phase 0 — Engineering Foundation](#phase-0)
2. [Phase 1 — Identity, Users, Pets, Species](#phase-1)
3. [Phase 2 — Credits, Funding, Rewarded Ads](#phase-2)
4. [Phase 3 — Private Cloud Media Pipeline](#phase-3)
5. [Phase 4 — Generic Cloud AI Platform](#phase-4)
6. [Phase 5 — Generic PETi Check](#phase-5)
7. [Phase 6 — Timeline, Measurements, Care, Notifications](#phase-6)
8. [Phase 7 — Veterinary Record Vault](#phase-7)
9. [Phase 8 — Dog Initial Scan](#phase-8)
10. [Phase 9 — Dental Check](#phase-9)
11. [Phase 10 — Feces Check](#phase-10)
12. [Phase 11 — Body Check](#phase-11)
13. [Phase 12 — Weekly PETi Report](#phase-12)
14. [Phase 13 — Premium / Google Play Billing](#phase-13)
15. [Phase 14 — Privacy, Deletion, Retention](#phase-14)
16. [Phase 15 — Observability, Economics, Operations](#phase-15)
17. [Phase 16 — Full Testing & Security Hardening](#phase-16)
18. [Phase 17 — Release Engineering / Play Submission](#phase-17)
19. [Scope Creep / Out-of-Spec Audit](#scope-creep--out-of-spec-audit)
20. [Consolidated Critical-Path Action Plan](#consolidated-critical-path-action-plan)

---

# Phase 0 — Engineering Foundation

- [x] `docs/ARCHITECTURE_INVARIANTS.md` exists, covers cloud-only AI, no Gemini in Android, cloud canonical, credits server-authoritative, no ambient ads, safety independence, species fail-closed — `docs/ARCHITECTURE_INVARIANTS.md:1-15`
- [x] "Costly operations measurable" invariant — `AnalysisService` now records observed input/output token units in the shared `CostAttributionService` for every successful analysis; the vertical-slice test asserts one cost record is associated with the completed job.
- [x] Provider usage normalization for cost attribution — Gemini/Vertex camelCase `usageMetadata` (`promptTokenCount`, `candidatesTokenCount`, `cachedContentTokenCount`, `requestId`) is normalized alongside local snake_case usage; both formats are tested.
- [x] Repo structure `android/`, `backend/`, `contracts/`, `eval/`, `infra/`, `scripts/`, `docs/` — confirmed present
- [x] Android modules `app`, `core:common`, `core:model`, `core:network`, `core:ui`, `core:testing` — included in `android/settings.gradle.kts` and compile successfully in the master Android build. Empty core bootstrap modules match the Phase 0 specification; feature-level source remains in the app/feature modules.
- [x] Build types debug/internal/release — `android/app/build.gradle.kts:12-33`
- [x] Backend directory layout (api/, auth/, config/, domain/, repositories/, services/, media/, ai/{providers,preparation,validation,guardrails}, safety/, credits/, advertising/, billing/, records/, care/, privacy/, operations/) — all present
- [x] Python 3.13+, FastAPI, Pydantic v2, pytest, ruff, mypy — `pyproject.toml:1-16`
- [x] `GET /health/live`, `/health/ready` — `backend/app/main.py:329-340`
- [x] API versioning under `/v1/` — `backend/app/api/v1.py:26`
- [x] Standard error envelope code/message/correlation_id/retryable — `backend/app/api/errors.py:17-25`
- [x] Correlation IDs on every request — middleware, error envelopes, response headers, Android adapters, and backend tests propagate `X-Correlation-ID`; distributed Cloud Tasks/log correlation remains external.
- [x] Structured logging with redaction — `backend/app/logging.py:9-29` (see Phase 15 for redaction coverage gaps)
- [x] `FakeAIProvider` with scenarios (SUCCESS/TIMEOUT/RATE_LIMIT/MALFORMED_OUTPUT/SAFETY_VIOLATION) — the provider wired by `main.py` accepts `FakeScenario` and is covered by `test_fake_provider_scenarios.py`; the legacy `app.services.ports.FakeAIProvider` remains a separate lightweight Phase-0 protocol fake.
- [x] Injectable Clock/IdGenerator — `backend/app/services/ports.py:14-48` (same wiring caveat: not used by `AnalysisService`)
- [x] `AnalysisOrchestrator` pipeline-order regression test — `backend/app/services/pipeline.py:4-20`, asserted `test_phase0.py:41-50`
- [x] `CloudCreditAccount`/`CloudCreditLedgerEntry`/`CostProfile`/`FundingDecision` domain skeletons — `backend/app/domain/foundations.py:43-72` (note: `LedgerDirection` here lacks `EXPIRE`, unlike the real Phase-2 enum in `credits/domain.py:35-41` — the two domain models have diverged)
- [x] No-Gemini-in-Android / no-direct-Firestore-in-Android automated gate — `scripts/architecture_check.py:1-11`
- [x] No-local-AI dependency gate (TFLite/LiteRT/TensorFlow) — `scripts/architecture_check.py` scans Android Gradle/version catalogs and rejects those dependency identifiers, in addition to the source-level cloud-only checks.
- [x] `.gitignore` protects secrets, `docs/SECRETS.md` exists
- [x] LOCAL/DEV/STAGING/PRODUCTION environments, no implicit production fallback — `backend/app/config/settings.py:7-11,63-95`
- [x] `./scripts/check.ps1` passes — current master evidence includes backend tests, Ruff, Mypy, architecture/secret checks, Android tests/lint/build, Terraform module and sandbox validation, and local evaluation gates.

### Recommended remediation tasks
1. Completed locally: correlation IDs, fake-provider scenarios, Android dependency architecture checks, deployment-contract tests, and credit-ledger enum consistency are implemented and covered by the current test/gate suite.
2. Remaining external gate: execute the same checks against the deployed GCP/Firebase topology, including Cloud Tasks authentication and multi-instance behavior.
3. Remaining external gate: collect physical-device accessibility, process-death, camera, localization, and account-switch evidence.

---

# Phase 1 — Cloud Identity, Users, Pets, Species Registry

- [x] Android Credential Manager + Firebase Auth (not legacy GoogleSignIn) — `android/app/src/main/java/com/peti/app/auth/FirebaseCredentialAuthRepository.kt:4-33`
- [x] Backend Firebase Admin verification via `IdentityVerifier` abstraction (`FirebaseIdentityVerifier`, `LocalTestIdentityVerifier`) — `backend/app/auth/verifiers.py:10-42`
- [x] `LocalTestIdentityVerifier` impossible to enable outside LOCAL — enforced via `Settings.validate_startup` (`config/settings.py:74`) and `main.py:105,132`
- [x] Canonical `User` domain (id, firebase_uid, role, billing_exempt, ads_exempt, internal_persona_code, timestamps) — `backend/app/domain/users.py:12-22`
- [x] `get_or_create_user` atomic/idempotent — `InMemoryUserRepository` uses a lock; `FirestoreUserRepository` uses a Firestore transaction when available and an `AlreadyExists` read-back fallback for lightweight adapters. Real multi-instance Firestore execution remains an external gate.
- [x] New users always CUSTOMER, exemptions false, client cannot influence role — `backend/tests/test_phase1_auth.py:19-26` (`X-Role: ADMIN` header ignored)
- [x] `AuthenticatedPrincipal` + `require_authenticated_principal()` dependency on protected routes — `backend/app/api/dependencies.py:6-29`
- [x] `GET /v1/me`, no sensitive fields exposed — `backend/app/api/v1.py:1549-1560`
- [x] `GET /v1/species`, `GET /v1/species/{code}/capabilities` — `v1.py:1563-1592`
- [x] `SpeciesCapabilityPack` profile_enabled is separate from AI enablement. DOG now has six explicitly enabled analysis types because the repository has progressed beyond the Phase-1 snapshot; this is an intentional maturity delta, not an implementation defect.
- [x] `AnimalProfile` generic model, not species-specific — `backend/app/domain/animals.py:11-19`
- [x] Full pet CRUD, owner-scoped, idempotent creation via Idempotency-Key, soft delete, species immutable — `v1.py:1595-1651`, `services/pets.py:17-72`; `PetPatch` (`v1.py:1531-1533`) has no `species` field
- [x] Ownership/anti-enumeration: non-owned pet → 404 not 403 — `services/pets.py:48-49`, tested `test_phase1_auth.py:9-16`
- [x] ADMIN/INTERNAL_TEST do not bypass ownership on ordinary routes — no role-based bypass code found; `test_real_admin_role_does_not_bypass_pet_ownership` covers ADMIN and INTERNAL_TEST principals.
- [x] Selected-pet Android local persistence scoped to PETi user_id with mismatch fallback — `android/app/src/main/java/com/peti/app/pets/SelectedPetStore.kt:12-31`
- [x] Backend integration tests for identity/species/pet/ownership — `test_phase1.py`, `test_phase1_auth.py`
- [x] Provisioning script for INTERNAL_TEST/ADMIN, not a customer API — defaults to Firestore via Application Default Credentials, supports explicit project selection, and retains `--local`/`--dry-run` for safe fixtures.

### Historical remediation record
1. Completed locally for the in-memory boundary: `get_or_create` is lock-protected and `test_concurrent_first_login_provisions_one_user` proves one identity/user. Firestore transaction contention remains an external emulator/deployment gate.
2. Completed locally: `scripts/provision_user_role.py` targets Firestore by default, supports explicit project selection, and retains `--local`/`--dry-run`; `test_build_repository_targets_firestore_by_default` verifies the real-store constructor boundary.
3. Completed locally: `test_real_admin_role_does_not_bypass_pet_ownership` verifies ADMIN and INTERNAL_TEST principals still get 404 on another user's pet and an empty owned list.
4. Completed locally: Phase-1 exit documentation now describes the current seeded DOG/CAT capability packs; historical Phase-1 build-plan language stating that empty AI capability lists are valid remains preserved as a design rule.

**Remaining external tests:** `test_concurrent_first_login_creates_one_user` against Firestore contention. The provisioning-constructor and admin-ownership regressions are now implemented locally.

---

# Phase 2 — Cloud Credits, Cost Classes, Funding, Rewarded Ads

- [x] `OperationType` enum — `backend/app/credits/domain.py:6-16`
- [x] `CostProfile` versioned/immutable — `credits/domain.py:44-57`, version bump in `credits/service.py:90-97`
- [x] `CreditGrant` with all 7 sources — `credits/domain.py:18-25,60-72`
- [x] `CreditLedgerEntry` immutable, append-only — `credits/domain.py:99-112`; never mutated/deleted anywhere in `credits/service.py`
- [x] `LedgerDirection` GRANT/RESERVE/CONSUME/RELEASE/EXPIRE/ADJUST — `credits/domain.py:35-41`
- [x] `CreditReservation` w/ statuses + multi-grant `Allocation[]` — `credits/domain.py:28-32,75-96`, proven by `test_phase2_credits.py:5-15`
- [x] `FundingQuote` non-reserving — `CreditService.quote` (`credits/service.py:187-209`) read-only
- [x] `RewardIntent`/`RewardedAdEvent` — `backend/app/advertising/domain.py`
- [x] APIs: quote, reservations, credits, credits/history, reward-intents, SSV callback — `v1.py:1416-1517,1654-1693`
- [x] Atomic reservation, concurrency test — in-memory reservation concurrency is covered by `test_phase2_credits.py`; Firestore uses a transaction in `credits/firestore_service.py`. A real emulator/multi-client contention run remains an external verification gate.
- [x] Reward SSV: signature check, dedup, one-transaction-one-grant, expired grants nothing — `advertising/google_ssv_verifier.py:20-44`, `advertising/service.py:48-84`; tested `test_google_ssv.py`, `test_phase2_rewards.py:5-23`
- [x] Client `onUserEarnedReward` does NOT mint credits — `android/.../funding/FundingModels.kt:49-58` (callback only resumes `true`), `FundingViewModel.watchAdAndRefresh` polls backend
- [x] Android no direct Firestore access to economic collections — `scripts/architecture_check.py:9` bans `firebase.firestore` string anywhere in Android (broader than required, but compliant)
- [x] `RewardedAdGateway` isolated to a funding feature module w/ architecture check — `:features:funding` now owns the gateway and Ads dependency; `:app` depends on that module, and `scripts/architecture_check.py` rejects Ads/`RewardedAdGateway` references outside the funding package. Gradle compilation remains subject to the current loopback/JVM environment gate.
- [x] `FakeRewardedAdGateway` for CI — `funding/FundingModels.kt:23-25`
- [x] `FakeRewardVerifier` for CI — `advertising/fake_verifier.py`; accepts only explicitly issued fixture tokens and is covered by `test_fake_reward_verifier.py`.
- [x] No ambient ads outside funding flow — `scripts/architecture_check.py` now fails Android source/build declarations that reference the Google Mobile Ads API or `RewardedAdGateway` outside `com/peti/app/funding/`.
- [x] Internal-only test-costly-operation harness — `scripts/credit_lifecycle_harness.py` exercises reserve/consume/release against `CreditService` with `INTERNAL_TEST` funding, performs an invariant audit, and never calls AI or external services.

### Recommended remediation tasks
1. **Completed locally:** `test_concurrent_reservation_race_one_wins_without_negative_balance` fires parallel reservation attempts against one grant balance; real Firestore contention remains external.
2. Keep the SSV round-trip test (`test_google_ssv.py`) aligned with Google's canonical signed-query format when the verifier contract changes.
3. Add an `architecture_check.py` rule (or Android lint rule) failing the build if any file outside `funding/` imports `com.google.android.gms.ads.*` or `RewardedAdGateway`.
4. Add an internal-only role-gated endpoint/CLI exercising reserve→consume/release end-to-end via the fake AI path.
5. When Android is split into real Gradle modules (Phase 0 remediation), isolate `funding` into its own module so ad-isolation becomes an enforceable build-graph constraint.

**Test status:** the reservation race, fake verifier, ad-isolation static check, and internal reserve/consume/release harness are implemented and included in the current local gate; real provider/Play execution remains external.

---

# Phase 3 — Private Cloud Media Pipeline

- [x] `MediaAsset` domain, all required fields — `backend/app/media/domain.py:54-92`
- [x] Media status state machine with illegal-transition rejection — `MediaAsset.transition` and `LEGAL_MEDIA_TRANSITIONS` are exercised by `test_phase3_media.py`.
- [x] Retention classes — `media/domain.py:21-27`, `media/retention.py:5-11`
- [x] `UploadStrategyResolver` — named abstraction in `media/upload_policy.py`, covered by `test_media_upload_policy.py`.
- [x] `StorageObjectNamer` — named abstraction produces opaque UUID-based names and is covered by media tests.
- [x] `ObjectStorage` abstraction, Gcs/Fake — `media/gcs_storage.py`, `media/storage.py`
- [x] APIs: upload-sessions (Idempotency-Key required), finalize, list, get, access, delete — `v1.py:1712-1820`
- [x] 🔴 Finalize authoritative (stat GCS, verify size/content-type/checksum) — size/content-type are verified from `stat_object()`, and production `GcsObjectStorage.checksum_object()` downloads canonical bytes and computes SHA-256; `test_media_gcs_checksum.py` covers the adapter boundary. Real GCS execution remains external.
- [x] Cross-user tests (finalize/read/delete denial) and signed-URL redaction — `test_phase3_media.py` and `test_logging_redaction.py` cover the local contracts; bucket IAM/public-access verification and production log-export review remain external/deployment gates.
- [x] Android Photo Picker + document picker (SAF), no broad permissions — `android/.../media/AndroidMediaSourceIntents.kt:8-14`, no `READ_EXTERNAL_STORAGE`/`READ_MEDIA_IMAGES` in manifest
- [x] CameraX photo/video capture — `CameraXCaptureDialog` embeds `PreviewView` and
  `CameraXCaptureController` owns `ImageCapture`/`VideoCapture`; the PETi Check
  capture buttons route through this flow. Physical camera permission, device
  behavior, and process-death evidence remain external device gates.
- [x] 🔴 WorkManager resilient upload with unique-work dedup — `MediaUploadCoordinator.scheduleRetry` uses `enqueueUniqueWork("peti-upload-$localId", ExistingWorkPolicy.KEEP, ...)`, preventing duplicate retry chains per upload.
- [x] Process-death recovery structure — `MediaUploadWorker.doWork()` rebuilds the coordinator from `applicationContext`; local Android build/test gates pass. Physical process-death execution remains external.
- [x] Abandoned upload cleanup — `RetentionService.expire_abandoned_uploads` expires stale `PENDING_UPLOAD`/`UPLOADING` assets, removes storage objects, updates sessions, and is covered by `test_phase3_retention.py`.

### Recommended remediation tasks
1. Completed locally: `MediaAsset.transition` now enforces legal transitions and `finalize` passes through `UPLOADING`/`UPLOADED_UNVERIFIED`; media state and checksum adapter tests cover the contract.
2. Completed locally: canonical checksum verification is covered by the GCS adapter boundary; real GCS execution remains external.
3. The unique retry chain is implemented as `peti-upload-$localId` with `ExistingWorkPolicy.KEEP`; remaining evidence is limited to device/process-death execution and backend abandoned-upload cleanup.
4. CameraX replacement is complete locally; physical camera framing/permission/device evidence remains external.
5. ✅ Implemented locally: `POST /v1/internal/tasks/media-maintenance` authenticates the dedicated maintenance task identity and runs both retention expiry and the abandoned `PENDING_UPLOAD`/`UPLOADING` sweep. Terraform now declares the hourly Cloud Scheduler OIDC job and IAM; apply/deployed execution remains an external gate.
6. Completed locally: cross-user access/delete denial and signed-URL redaction are covered by `test_phase3_media.py` and `test_logging_redaction.py`.

**Tests to add:** `test_media_state_machine_rejects_illegal_transitions`, `test_finalize_checksum_mismatch_real_gcs_blob`, `test_unique_work_prevents_duplicate_upload_on_retry`, `test_process_death_recovery_no_duplicate_asset`, `test_abandoned_upload_cleanup_expires_stuck_sessions`, `test_cross_user_media_access_denied`, `test_cross_user_media_delete_denied`, `test_signed_url_absent_from_logs`.

---

# Phase 4 — Generic Cloud AI Platform

- [x] Cloud Tasks queue abstraction — `backend/app/analysis/queue.py`
- [x] Private worker entrypoint requiring OIDC — `backend/app/main_worker.py:19-33`; deployment-level isolation confirmed (`infra/terraform/modules/peti-platform/main.tf:201` `INGRESS_TRAFFIC_INTERNAL_ONLY` vs. `:299` `INGRESS_TRAFFIC_ALL` for the public API), and a bounded real Cloud Tasks OIDC health task returned HTTP 200.
- [x] 🔴 Customer Firebase token rejected by worker route — `test_worker_surface.py` posts a Firebase-shaped bearer token through the private worker `TestClient` and asserts `401 TASK_SERVICE_IDENTITY_INVALID`; public API route exposure remains an external deployment/design decision to review.
- [x] `AnalysisJob` state machine — `analysis/domain.py:22-62`, `LEGAL_TRANSITIONS`/`transition()`, enforced again at repository layer
- [x] `AnalysisResult` provenance fields — `analysis/domain.py:102-128`
- [x] 🔴 Idempotency / duplicate Cloud Task delivery — in-memory and Firestore repositories claim only `QUEUED`/`FAILED_RETRYABLE` jobs and atomically mark them `PREPARING_MEDIA`; duplicate-claim coverage exists in `test_analysis_claim_concurrency.py` and `test_firestore_analysis_repositories.py`. Production evidence still requires a real Firestore transaction run.
- [x] `MediaPreparer` versioned, per-modality — dispatcher and named image/video/audio/document preparers are implemented and covered by `test_phase45_platform_boundaries.py`; provider-specific transforms remain provider/runtime work.
- [x] 🔴 Prompt registry: versioned files + content-hash detects in-place edits — `ai/registry.py` loads active prompts/schemas from versioned files, hashes immutable registrations, and `test_prompt_registry_files.py` verifies the active contents match disk artifacts.
- [x] Output schema registry versioned — `ai/registry.py:64-88` (same file/hash-not-linked caveat as prompts)
- [x] `GeminiProvider` implementing `AIProvider`, server-only credentials — `ai/providers/gemini.py:13-76`
- [x] Provider error normalization — Gemini and Fake providers share `PROVIDER_TIMEOUT`, `PROVIDER_RATE_LIMITED`, `PROVIDER_UNAVAILABLE`, and permanent `PROVIDER_REQUEST_FAILED` taxonomy; scenario tests cover the retryable classifications.
- [x] `SemanticGuardrail`/`GuardrailPipeline` applied generically — `AnalysisService.process` recursively scans every provider payload, including `PLATFORM_MULTIMODAL_SMOKE`; `test_generic_analysis_applies_semantic_guardrails` covers the integration.
- [x] 🔴 Deterministic, provider-independent `SafetyEngine` that cannot be downgraded by the model — `AnalysisService.merge_safety` selects the highest defined severity and is covered by `test_safety_precedence.py`; unknown model states cannot override the deterministic decision.
- [x] Funding consumption boundary (reserve→consume once, release before boundary) — `consume` called only after `provider_accepted` (`service.py:264-266`); `release` only in the pre-boundary except branch (`service.py:367-371`)
- [x] AI kill switches: global/per-provider/per-model/per-analysis-type/per-species — global and scoped runtime switches gate `process()`; ADMIN-only controls persist through `FirestoreFeatureFlagStore` when Firestore is configured, and local mode remains explicitly in-memory. Durable production audit records, multi-instance deployment drill, and propagation evidence remain external.
- [x] Android: no Gemini/Google AI SDK dependency — enforced by `scripts/architecture_check.py` and the Android architecture gate; `com.google.ai.*`, `generativeai`, and local model SDK markers are rejected.

### Recommended remediation tasks
1. Completed locally: worker analysis/specialist surfaces reject Firebase-shaped customer bearer tokens in `test_worker_surface.py`.
2. Completed locally: repository claim uses atomic status transitions and duplicate-claim tests cover in-memory and Firestore adapters; real Firestore execution remains external.
3. [x] Wire the actual `.md`/`.json` files in `ai/prompts/`/`ai/schemas/` into `ImmutableRegistry`; the registry loads and hashes the versioned files and tests verify active content matches.
4. Completed locally: deterministic safety merge only permits escalation and rejects unknown/downgrading model states; `test_safety_precedence.py` covers the integration.
5. Completed locally: `EconomicsPolicy` and emergency variable-cost intake are wired into analysis/operations and covered by `test_ai_kill_switch.py`.
6. Completed locally: `scripts/architecture_check.py` and the Android architecture gate fail the build on any `com.google.ai.*`/`generativeai` dependency.
7. Completed locally: provider errors normalize to the documented retryable/permanent taxonomy; scenario tests cover the classifications.
8. [x] Confirm the public API task routes are intentional compatibility surfaces: every route is protected by dedicated task-identity authentication, while the Cloud Run worker has a separate private ingress entrypoint. Deployment contract tests cover the separation; live ingress/IAM verification remains an external gate.

**Remaining gates:** equivalent local worker-authentication, worker-surface, safety-precedence, kill-switch, and prompt-registry tests pass; duplicate-delivery behavior and deployed multi-instance Cloud Tasks/public-ingress verification remain external or require additional integration evidence. Prompt-file loading is covered by `test_prompt_registry_files.py`.

---

# Phase 5 — Generic PETi Check

- [x] `PETI_CHECK` restricted to DOG, no fallback — `repositories/memory.py:35-50`, `analysis/service.py:103-106`, remapped `v1.py:1361-1363`
- [x] `PetiCheckResultV1` strict schema — canonical `GOOD/PARTIAL/INSUFFICIENT` evidence levels and structured `EvidenceQuality` are enforced in `peti_check/contracts.py`; legacy `HIGH/MEDIUM/LOW` values are normalized at the provider boundary, while the persisted safety contract remains the phase-specified `safety_state` plus deterministic reasons.
- [x] Guardrails scan every visible string field — both the pipeline and legacy `validate_peti_check` now delegate to recursive `validate_payload_text`; the legacy entry point additionally preserves `DIAGNOSIS_IN_OBSERVATION` compatibility.
- [x] Excessive-certainty vs `evidence_quality` mismatch guardrail — implemented in typed and recursive PETi Check validation; red-team tests cover low/partial evidence and high-evidence controls.
- [x] 🔴 Deterministic `PetiCheckSafetyPolicy`, model cannot downgrade — `evaluate_safety` recognizes PETi Check states and `AnalysisService.merge_safety` combines deterministic and model states by maximum severity; `test_safety_precedence.py` covers urgent override, review escalation, unknown-state rejection, and clear preservation.
- [x] Abstention (`INSUFFICIENT_EVIDENCE`) is a valid COMPLETED result — `analysis/service.py:341-346`
- [x] No ad ever to re-open a completed result — read-path regression test verifies result reads do not touch the funding service; read endpoints are pure reads by construction.
- [x] Feature flags server-controlled — `possible_interpretations_enabled` is configured in settings, passed through `main.py`, and enforced in `AnalysisService`; the disabled path is tested.
- [x] History API, reopening doesn't re-run AI — `v1.py:1367`, read-only handler confirmed
- [x] Red-team fixtures — exact-temperature, prompt injection, certainty mismatch, and specialist-language leakage are covered by `test_peti_check_red_team.py`; real held-out/red-team provider execution remains external.

### Recommended remediation tasks
1. Completed locally: PETi Check safety vocabulary, evidence-quality normalization, certainty guardrail, legacy validator delegation, and server-controlled interpretations flag are covered by the contract and red-team suites.
6. Add red-team fixtures for contradictory owner context and specialist-leakage (teeth/stool photo through generic Check); add an explicit "reopen never touches credits/ads" test.

**Tests to add:** `test_peti_check_clear_result_stays_clear_not_insufficient` (regression for #5 above — highest priority), `test_evidence_quality_certainty_mismatch_rejected`, `test_possible_interpretations_flag_gates_field`, `test_contradictory_owner_context_red_team`, `test_no_specialist_leakage_through_generic_check`, `test_reopen_result_no_funding_no_ad`.

---

# Phase 6 — Timeline, Measurements, Care, Reminders, Notifications

- [x] Timeline is a derived projection (not duplicated storage) — `backend/app/phase6.py:733-787`, PETI_CHECK/DocumentedFact items assembled on read at `api/v1.py:1060-1114`; pagination is timestamp-based keyset (`before`/`after`), acceptable but not literally opaque-cursor
- [x] `MeasurementRecord` with `measurement_type`/`source_class` enums — `phase6.py:18-27,82-97`
- [x] Client cannot create `AI_ESTIMATED` — enforced server-side and covered at service and FastAPI HTTP levels (`test_phase6.py`, `test_phase7_api_e2e.py`).
- [x] Original value/unit preserved exactly, normalized stored separately — `phase6.py:89-92`, golden test `test_phase6.py:46-52`
- [x] Deterministic unit conversion library — `phase6.py:69-79`; °F↔°C, kg↔lb and round-trip precision vectors are covered by `test_phase6.py`.
- [x] Conflicting measurements coexist — no update/merge path exists at all (only create+soft-delete), so silent overwrite is structurally impossible
- [x] Measured-only trend filter separate & explicit, default OFF for AI estimates — `measurement_trend(..., include_ai_estimates=False)` (`phase6.py:410-427`)
- [x] No route/copy implies phone/camera measures core temperature — grepped; explicit `docs/adr/ADR-042-manual-temperature-only.md` and Android copy confirms
- [x] Care/Occurrence/RecurrenceRule domain, idempotent+bounded occurrence generation — `phase6.py:99-134,451-472` (only materializes the single next occurrence, never a future batch)
- [x] Care due/overdue correct independent of notification permission — `occurrence_status()` (`phase6.py:546-554`) computed purely from `due_at` vs `now`; `dispatch_due()` filters permission for delivery only, not status computation
- [x] `NotificationDelivery` with dedup key — `phase6.py:161-171,681-702`
- [x] FCM token registration bound to authenticated user, not logged — `phase6.py:593-647`

### Recommended remediation tasks
1. Completed locally: °F↔°C, kg↔lb and round-trip precision vectors are in `test_phase6.py`.
2. Completed locally: FastAPI HTTP-level rejection of client-created `AI_ESTIMATED` measurements is in `test_phase7_api_e2e.py`.
3. Completed locally: overdue status remains independent of denied notification permission in `test_phase6.py`.

**Tests to add:** `test_unit_conversion_golden_vectors_fahrenheit_celsius`, `test_measurement_ai_estimated_rejected_http_level`, `test_care_overdue_correct_with_notifications_denied`.

---

# Phase 7 — Veterinary Record Vault

- [x] `VeterinaryDocument` reusing Phase-3 media, `retention_class=CLINICAL_DOCUMENT` — `backend/app/records/vault.py:64-78,192-203`
- [x] `CandidateFact` never auto-promotes — verified no code path sets `CONFIRMED`/creates a `DocumentedFact` except through `review()` (`vault.py:348-385`), requiring explicit human action via `v1.py:842-853`
- [x] `SourceAnchor` traceability — `vault.py:54-61`
- [x] Reject is terminal — `vault.py` raises `CANDIDATE_FACT_ALREADY_REVIEWED` for any second review; dedicated regression coverage is in `test_phase7_records.py`.
- [x] Correct preserves both original and corrected value — `vault.py` never mutates `candidate_value`, `CandidateFactReview.corrected_value` stores the correction separately; test `test_phase7_records.py:64-73`
- [x] APIs: records CRUD, access, extract, candidate-facts, confirm/correct/reject — `v1.py:753-855`
- [x] AI extraction produces CandidateFacts, real provider path deliberately blocked from customer API — `vault.py:312-346` (local fixture only), `v1.py:817-821` explicitly returns `503 RECORD_EXTRACTION_NOT_AVAILABLE` for real extraction — consistent with the project's own honesty disclaimer.
- [x] 🔴 Deletion dependency handling / cascade — uses the explicit `source_document_id` foreign-key field, ignores owner-edited notes, and has both positive linked-`DOCUMENTED` and negative unrelated-`MEASURED` tests in `test_phase7_records.py`.
- [x] No candidate fact ever appears in Timeline before review — implemented (`v1.py:1084-1102` only pulls confirmed `DocumentedFact`s); API and record-flow tests cover the candidate-only boundary.

### Recommended remediation tasks
1. Completed locally: `Measurement.source_document_id` is explicit and cascade logic uses the foreign key rather than editable notes.
2. Completed locally: positive linked documented-measurement deletion coverage is in `test_phase7_records.py` and the API flow.
3. ✅ Added HTTP regression coverage proving PENDING_REVIEW/REJECTED candidates never appear in `GET /v1/pets/{pet_id}/timeline`.
4. Completed locally: rejected candidates are terminal and a second review raises `CANDIDATE_FACT_ALREADY_REVIEWED`.
5. When real AI/OCR extraction is implemented, route it exclusively through the already-stubbed worker/task-authenticated path, preserving the candidate-only invariant.

**Relevant tests:** `test_measurement_source_document_id_field_not_notes_substring`, `test_delete_document_cascades_linked_documented_measurement` (positive case), the Phase 7 HTTP timeline visibility regression, and `test_rejected_candidate_cannot_be_reconfirmed`.

---

# Phase 8 — Dog Initial Scan

- [x] `DOG_INITIAL_SCAN` type, DOG-only server-side — `specialists/service.py:24,161-167`, tested `test_specialists_phase8_10.py:42-45`
- [x] `InitialScanCandidate` w/ full review-status lifecycle — `specialists/service.py:114-127,533`
- [x] 🔴 Candidates write only after explicit review — `AnimalProfile` now carries allowlisted coat/breed/life-stage fields and `profile_field_provenance`; `review_initial_candidate` reads the server-side profile, rejects stale confirmation conflicts, and applies only CONFIRMED/CORRECTED values through `PetService.update_profile_fields`. Reject/skip remain non-mutating.
- [x] Hard guardrail — reject exact age/weight/neuter/spay/ancestry/health — `specialists/service.py:61-64,272-291`, tested `test_specialists_phase8_10.py:28-39`
- [x] Breed certainty guardrail — Initial Scan now removes candidate text containing "breed certainty", "definitely a", "certainly a", "100%", "purebred", or equivalent prohibited certainty language, marks the result `RESTRICTED`, and retains only cautious suggestion wording. Adversarial coverage is in `test_specialist_forbidden_variants.py`.
- [x] Conflict path (existing value vs. suggestion, both shown, user chooses) — server-side conflict detection and confirm/correct persistence are tested; Android now exposes per-candidate Confirm, Correct (editable value), Reject, and Skip actions with stable test tags. The server remains authoritative for the actual current value.
- [x] `ProfileFieldProvenance` — represented by the canonical `AnimalProfile.profile_field_provenance` map with `USER_CONFIRMED`/`USER_CORRECTED` values; `AI_SUGGESTED` remains the candidate's pre-review provenance.

### Recommended remediation tasks
1. Add breed/coat/life-stage fields to `AnimalProfile` plus a `ProfileFieldProvenance` enum; wire `review_initial_candidate`'s confirm/correct paths to actually write through `pets.update()` with provenance; test reject/skip never mutate the profile and confirm/correct do, with correct provenance tag.
2. Execute the real Initial Scan red-team suite against the approved Gemini configuration; local guardrail coverage is complete but external execution remains pending.
3. Make `INITIAL_SCAN_PROFILE_CONFLICT` compare against a real, server-stored value; add a regression test for the conflict path.
4. Add server-backed current-value display beside each Android suggestion when the profile API exposes it.

**Tests to add:** `test_confirm_initial_scan_candidate_writes_profile_with_provenance`, `test_reject_skip_never_mutate_profile`, `test_breed_certainty_language_rejected`, `test_profile_conflict_uses_server_side_value_not_client_supplied`.

---

# Phase 9 — Dental Check

- [x] `DOG_DENTAL_CHECK` type, DOG-only — `specialists/service.py:25,166`
- [x] Independently feature-flagged — `operations/platform.py:80-94`, enforced `service.py:234-238`
- [x] `visible_findings[]` restricted to controlled taxonomy — `service.py:70-75,298-311`, tested (enum-filtering only)
- [x] 🔴🔴 Hard prohibited Dental claims — dental output is passed through `_guardrail_result` before normalization, with natural-language and underscore variants for periodontal stage, pocket depth, root/bone, pulp, abscess, infection, diagnosis, medication, and hidden-disease claims; `test_specialist_guardrails.py` and `test_specialist_forbidden_variants.py` cover the safety boundary. Real red-team execution remains external.
- [x] Deterministic safety escalation not downgradable by model — `_dental_safety` (`service.py:268-279`) unions owner context with model red-flags only to escalate; dedicated urgent/prompt/review/monitor tests are in `test_specialist_guardrails.py`.
- [x] `areas_not_assessed` field present (minor naming drift from spec's `areas_not_assessable`) — `service.py:317`
- [x] Capture safety copy — `android/.../SpecialistPanel.kt:29-32`
- [ ] Release certificate — the `release/evaluation/DOG_DENTAL_CHECK_RELEASE_CERTIFICATE.md` artifact exists and explicitly remains `PENDING_EXTERNAL_GEMINI`; runtime specialist release validation now fails closed whenever the configured certificate ID is `PENDING`. The certificate cannot be promoted until held-out/red-team/provider/device evidence is produced.

### Recommended remediation tasks — HIGHEST PRIORITY IN THE ENTIRE AUDIT
1. **Completed locally:** `DOG_DENTAL_CHECK` passes through `_guardrail_result` in both creation and task completion paths.
2. **Completed locally:** dental forbidden-claim matching covers natural-language and underscore variants, including abscess and hidden-disease reassurance.
3. **Completed locally:** dedicated dental guardrail and forbidden-variant tests cover periodontal stage, pocket depth, root/bone, pulp, abscess, and reassurance wording.
4. Wire `eval/specialists/dog_dental_check/*.json` fixtures into a real CI-run harness (mirror `eval/peti_check/run_red_team.py`) and produce a genuine release certificate before flipping the certificate ID off `PENDING`.

**Test status:** the local wiring and claim-variant tests are implemented and passing; only the real CI/provider certificate harness remains pending.

---

# Phase 10 — Feces Check

- [x] `DOG_FECES_CHECK` type, DOG-only — `service.py:26,166`
- [x] Multi-dog producer attribution fails closed (P10-INV-004) — `service.py` rejects unconfirmed target dogs; dedicated regression coverage is in `test_specialists_phase8_10.py`.
- [x] Own non-proprietary consistency taxonomy — `service.py:92`, matches spec exactly
- [x] Hard prohibited feces claims — `_guardrail_result` uses explicit parasite/worm species, infection, dehydration, medication, and causal-claim variants; specialist guardrail tests cover adversarial wording. Real Gemini red-team execution remains external.
- [x] `NOT_OBSERVED ≠ absence` phrasing — normalization now replaces overclaiming provider text for `NOT_OBSERVED` worm-like findings with sanctioned visible-observation wording; regression coverage is in `test_specialists_phase8_10.py`.
- [x] Deterministic safety escalation on tarry/blood, escalation-only union — tarry and fresh-red-blood paths are covered by `test_specialists_phase8_10.py`; model/context signals only escalate safety.
- [x] Longitudinal comparison doesn't imply progression — effectively moot: `dog_feces_longitudinal_compare_enabled` defaults **False** (`operations/platform.py:106`), so comparison always returns `FECES_CHECK_COMPARISON_NOT_AVAILABLE`. NEW/IMPROVED/STABLE/WORSENED/NOT_COMPARABLE logic is implemented only for Body Check, not Feces at all.

### Recommended remediation tasks
1. [x] `FECES_FORBIDDEN_TEXT` includes named parasite variants and dehydration forms; specialist guardrail tests cover these variants.
2. [x] Pytest coverage covers the multi-dog fail-closed path (P10-INV-004) and fresh-red-blood escalation.
3. [x] Regression coverage asserts that `NOT_OBSERVED` worm-like findings use sanctioned phrasing.
4. [x] Feces longitudinal comparison is intentionally deferred and remains disabled by default; enabling it requires a separately reviewed implementation and progression-language certification.

**Tests to add:** `test_feces_multi_dog_ambiguous_producer_fails_closed`, `test_feces_named_parasite_variants_rejected` (roundworm/tapeworm/etc), `test_feces_dehydration_word_form_rejected`, `test_feces_fresh_blood_escalation`, `test_feces_not_observed_uses_sanctioned_phrasing`.

---

# Phase 11 — Body Check

- [x] `DOG_BODY_CHECK` type, DOG-only — `service.py:27,166`
- [x] Controlled observation taxonomy, not a reproduced BCS chart — `service.py:84-85` (deliberately non-numeric `LEAN_APPEARANCE`/`BALANCED_APPEARANCE`/`ROUNDED_APPEARANCE`/`UNCERTAIN`)
- [x] Hard prohibited Body Check claims — `BODY_FORBIDDEN_TEXT` includes the generic `diagnos` stem plus exact-age, reproductive, body-fat, certainty, and disease-related terms; Body Check regression tests cover diagnostic filtering.
- [x] AI weight estimate structurally cannot become MEASURED / cannot leak into trend filter — **ROBUSTLY IMPLEMENTED, by isolation** — `phase6.py:278-279,425-426` rejects client-submitted `AI_ESTIMATED` and excludes it from trends by default; separately, **no bridge code exists at all** connecting `specialists/service.py`'s `ai_weight_estimate` output to `phase6.py`'s `Measurement` creation — the two systems are entirely disjoint, satisfying the invariant by isolation rather than an explicit type-level guard.
- [x] Default-disabled sub-capability pending calibration — `dog_body_ai_weight_estimate_enabled: False` (`operations/platform.py:112`); no calibration evidence artifact exists (correctly conservative).
- [x] Same-dog-only longitudinal comparison, pose/lighting mismatch → NOT_COMPARABLE — `service.py:552-586`
- [x] Phase 11 local regression coverage — `test_specialists_phase8_10.py` covers allowlisted observations, default-disabled category/estimate flags, AI-estimate provenance/limitations, and diagnostic-claim restriction. Real Gemini/device certification remains external.

### Remaining remediation gates
1. Local Body Check enforcement, forbidden-text filtering, estimate isolation/provenance, default-disabled flag behavior, and capture validation are covered by `test_specialists_phase8_10.py` and `test_specialist_forbidden_variants.py`.
2. Executable held-out/red-team fixture runs and calibration evidence remain external provider/device gates.

---

# Phase 12 — Weekly PETi Report

**Current evidence:** dedicated weekly-report tests exist in `test_weekly_report_narration.py` and `test_weekly_report_timezone.py`; real scheduler/provider/device execution remains external.

- [x] 🔴 Idempotent one-report-per-(animal_id, week_key, policy_version) — `WeeklyReportService` uses an idempotency key under an `RLock`; local report generation and duplicate-dispatch behavior are covered. Multi-instance Firestore uniqueness remains an external staging gate.
- [x] 🔴 Deterministic, timezone-aware week-key policy — uses `zoneinfo.ZoneInfo`, deterministic UTC fallback, and account-local week boundaries; timezone tests cover the boundary and invalid-zone behavior.
- [x] 🔴🔴 Distinct `MEANINGFUL_CHANGE` / `NO_MEANINGFUL_CHANGE` / `NOT_ENOUGH_DATA` states — implemented in `WeeklyReportService.generate` and covered by `test_weekly_report_timezone.py`.
- [x] Source-reference traceability on material claims — `WeeklyReportService.validate()` computes `material_claim_source_traceability`; `test_weekly_report_timezone.py` verifies source references and validation before persistence.
- [x] Deterministic core requires no Gemini; optional narration is now guarded by `WeeklyReportNarrationValidator`: unknown source references, diagnostic/prognostic/prescription language, unsupported schema versions, and urgency downgrades are rejected. Real Gemini narration execution remains an external gate.
- [x] Report viewing never requires ad/credit — read path is independent of funding and covered by the report read regression.
- [x] Historical reports immutable, reopen never regenerates — `get()`/`list()` never call `generate()`; the regression test fails if reading invokes the timeline generator.

### Recommended remediation tasks
1. Completed locally: timezone-aware week keys and DST boundary behavior are covered by `test_weekly_report_timezone.py`.
2. Completed locally: `NO_MEANINGFUL_CHANGE` is distinct from `NOT_ENOUGH_DATA` and both states are covered by the weekly report tests.
3. Completed locally: duplicate identity, traceability, immutable read and no-funding read-path coverage exists across the weekly report test files; multi-instance scheduler execution remains external.
4. Completed locally: `WeeklyReportService.dispatch_week()` now wires `WeeklyReportDispatcher` for idempotent scheduler/operator delivery, and `reconcile_sources()` wires `WeeklyReportReconciler`; `test_weekly_report_dispatch.py` covers duplicate suppression and missing-source detection. Concurrent multi-instance execution remains external.
5. If narration ships, run the validator against real Gemini held-out output and bind the evidence to the release configuration.

**Remaining external test:** concurrent multi-instance scheduler/reconciler execution against the deployed store.

---

# Phase 13 — Premium / Google Play Billing

**Current evidence:** backend and Android billing boundaries have dedicated local security/concurrency coverage; real Play product, RTDN and license-tester execution remains external.

- [x] Backend is sole entitlement authority and fails closed without server verification — non-LOCAL environments reject client trust flags; exact configured package names are required; local trust is explicitly test-only. Real Google Play Publisher API wiring and execution remain external release gates.
- [x] Purchase token uniqueness / replay rejection — `billing/premium.py:74-76`; cross-account token conflict and replay behavior are covered by `test_premium_concurrency.py`.
- [x] RTDN is a trigger only and re-fetches canonical state through the injected verifier; missing verifier, invalid payload, and owner mismatch fail closed. Real Play/RTDN delivery remains pending external evidence.
- [x] RTDN duplicate-message idempotency — `billing/rtdn.py:28-43`, dedups by `event_id`; local replay coverage is present, while high-volume duplicate delivery remains an external integration gate.
- [x] Entitlement state mapping (ACTIVE/GRACE retain, HOLD removes but app works, CANCELED-entitled retains, EXPIRED/REVOKED removes without deleting data) — `billing/google_play.py` and `billing/premium.py` map the full matrix; `test_premium_concurrency.py` now covers all six states plus token ownership conflict.
- [x] Idempotent premium allowance grants — `PremiumService` now owns and invokes `PremiumAllowanceService` for active/in-grace entitlements using the current `YYYY-MM` period key; duplicate reconciliation remains a single grant, covered by `test_premium_concurrency.py`.
- [x] No local/client Premium override in release build — Android now has a
  Play Billing Library 7.1.1 client boundary (`PlayBillingClientGateway`) that
  only forwards purchase/restore tokens to the server reconciliation port; it
  never grants entitlement locally. Real Play product and license-tester
  execution remains an external gate.

### Remaining remediation gates
1. Real Google Play Developer API credentials, products, RTDN delivery and license-tester subscriptions remain required for live verification.
2. The local security fixes, reconciliation boundaries, state matrix, concurrency tests and Android Play Billing client boundary are implemented and covered by the existing billing suites.

**Test status:** the listed trust-boundary, verifier, RTDN, token-conflict, duplicate-delivery, state-matrix, and premium-expiry tests are implemented in the current billing suites; live Play/RTDN execution remains external.

---

# Phase 14 — Privacy, Deletion, Retention Lifecycle

**Current evidence:** privacy dependency, residual-verifier and identity-tombstone tests provide dedicated local coverage; live deletion races remain external.

- [x] `DeletionRequest`-equivalent staged lifecycle — `privacy/lifecycle.py:21-29,76-112` (`AccountDeletionJob`), matches the required state-machine shape for whole-account deletion; **no explicit per-scope `DeletionRequest` for partial deletions** (e.g., deleting a single record independent of account deletion) beyond ad-hoc calls in service code.
- [x] `DeletionDependencyResolver` models the canonical cross-entity chain and the deletion cascade now consumes the plan's domain set before invoking adapters; omitted domains cannot be silently deleted by the cascade. Cloud-backed residual/race execution remains an external gate.
- [x] Deletion never requires ad/Premium/credits — confirmed, `delete_account` checks only a `confirm: bool` flag.
- [x] Premium/billing state never blocks deletion — confirmed by the deletion gate path and `test_privacy_dependencies.py`; premium remains an independent entitlement domain.
- [~] Pending Cloud Tasks for deleted target no-op — `PrivacyService` now drives freeze/cancel state-machine steps before deletion; registered local work returns `NO_OP/ACCOUNT_DELETED`, and local gate coverage exists in `test_identity_tombstone.py`. Wiring the shared gate into the deployed Cloud Tasks handler and canceling provider-enqueued tasks remains an external integration gate.
- [x] 🔴 GCS + Firestore residual verification has an independent media inventory — `MediaStorageResidualInventory` derives owner-scoped Firestore metadata and probes each canonical storage object; caller-supplied counts cannot override it. Other domain inventories and real deployed IAM/execution remain external gates.
- [x] FCM/device tokens removed on account deletion — `Phase6Service.remove_device_registrations()` removes device registrations and notification deliveries from memory and the backing store; account deletion invokes it.
- [x] Same Firebase identity signing back in does not resurrect deleted data — user tombstones are consulted by both memory and Firestore `get_or_create`; covered by `test_identity_tombstone.py`. Real Firebase reinstall execution remains external.

### Recommended remediation tasks
1. Make `_perform_delete_account` actually consult `DeletionDependencyResolver.dependencies()` instead of a hand-rolled sequence; extend the resolver to the full documented chain.
2. Implement a real Cloud Tasks cancellation adapter for `CANCEL_QUEUED_WORK`; add a queued-task/delete-before-delivery race test.
3. Extend `MediaStorageResidualInventory` with independent inventories for each remaining canonical Firestore domain and run the reconciliation against deployed GCS/Firestore; the media object gate is now implemented locally, while full production inventory evidence remains external.
4. Add FCM/device token removal to the deletion path.
5. Add a "re-sign-in with same Firebase identity doesn't resurrect data" regression test; add an identity-tombstone mechanism if none exists.
6. Add `backend/tests/test_privacy_deletion.py` covering: delete-while-Premium-active, delete-with-queued-task race, residual-verification failure/retry, post-deletion re-signup isolation.
7. **Full GCS/Firestore residual-zero verification requires a real GCP project**; the dependency-graph wiring, Cloud-Task no-op adapter, and FCM cleanup are all fixable purely in code today.

**Test status:** local coverage exists for dependency planning, queued-work freeze/no-op, independent residual inventories, FCM/device cleanup, active-premium deletion, and identity tombstones; live multi-service race and residual-zero execution remain external.

---

# Phase 15 — Observability, Economics, Production Operations

- [x] Correlation IDs propagated end-to-end at the local boundary — backend middleware/request envelopes and analysis creation carry the request ID; all Android `HttpURLConnection` adapters now generate and send `X-Correlation-ID`, enforced by `scripts/architecture_check.py`. Cloud task/log correlation and production trace export remain deployment evidence gates.
- [x] 🔴 Structured log redaction — `JsonFormatter` redacts bearer-shaped tokens, signed URLs, keys, and all registered sensitive fields; sentinel tests cover purchase, FCM, device, Firebase, and signed-URL values. Production log-export verification remains external.
- [x] Bounded-cardinality metric dimensions with a CI check — `scripts/check_metric_cardinality.py` validates the payload-free monitoring contract and is invoked by both `scripts/check` and `scripts/check.ps1`.
- [x] `AICostRecord` per analysis — `operations/platform.py:37-51,176-183` — the **strongest-tested item across all four of these phases** (`test_analysis_cost_metadata.py`).
- [x] Server-authoritative kill switches — new work fails closed and releases funding; completed historical results return before the kill-switch branch. `test_ai_kill_switch.py` covers both behaviors.
- [x] Emergency spend-cap switch — `operations/platform.py:147-162` gates new intake without touching credits or safety; dedicated ADMIN/fail-closed coverage is in `test_ai_kill_switch.py`.
- [x] Idempotent reconciliation (`ReconciliationService.reconcile`) — genuinely idempotent, cached `COMPLETE` result short-circuits re-invocation; `test_queue_reconciliation.py` exists — real coverage.

### Recommended remediation tasks
1. Completed locally: API analysis creation passes `request.state.correlation_id` into `AnalysisService.create()`; the analysis domain, task payloads and structured request logs preserve it. An Android interceptor and deployed end-to-end trace evidence remain external follow-up gates.
2. Completed locally: structured logging redacts Firebase tokens, GCS signed URLs, Play purchase tokens, FCM/device tokens, and registered sensitive fields; production log-export review remains external.
3. Completed locally: `backend/tests/test_logging_redaction.py` injects sentinel JWT, signed-URL, purchase-token, FCM-token, device-token, and Firebase-token values and asserts they are absent from serialized JSON.
4. Completed locally: `scripts/check_metric_cardinality.py` rejects forbidden high-cardinality labels and is included in `scripts/check.ps1`/`scripts/check`.
5. Completed locally: `test_ai_kill_switch.py` exercises new-analysis rejection/funding release and confirms historical results remain readable while the switch is off.

**Remaining gate:** the local end-to-end correlation test passes; deployed trace evidence across the Android client, API, queue, worker, and exported logs remains external.

---

# Phase 16 — Full Testing, Security Hardening, Release-Candidate Certification

- [x] `release/RC_MANIFEST.json` exists — status `SOURCE_READY_EXTERNAL_CERTIFICATION_PENDING`, `tests_executed: false`, `provider: UNVERIFIED`
- [x] `release/REQUIREMENTS_TRACEABILITY_MATRIX.md` exists — but only phase-range granularity, not domain-level
- [x] `release/EVIDENCE_MANIFEST.json`, `release/RC_BLOCKERS.md`, `release/PHASE16_CERTIFICATION_REPORT.md` exist and are honest about NO-GO status
- [x] Local cross-user authorization matrix for the root pet CRUD surface — `test_customer_crud_operations_are_cross_user_isolated` covers GET/list/PATCH/DELETE for a second CUSTOMER; domain-specific matrices and real Firestore execution remain external/remaining scope.
- [x] Funding: duplicate reservation idempotency — `test_phase2_credits.py:5`
- [x] Funding: reward SSV replay/forgery — `test_phase2_rewards.py:10-20`
- [x] Funding: true concurrency/race test — `test_phase2_credits.py` runs 12 simultaneous reservation attempts and verifies one winner/no negative balance.
- [x] Premium grant concurrency test — `test_premium_concurrency.py` covers concurrent entitlement reconciliation and package fail-closed behavior.
- [x] Android artifact inspection — `scripts/inspect_release_artifact.py` is wired
  into `.github/workflows/phase0.yml`, inspects the generated debug APK payload
  (not only filenames), and preserves a strict production mode that rejects the
  intentional `local-test:` marker.
- [x] Accessibility regression suite — `AccessibilityRegressionTest` verifies
  operable sign-in, editable pet-name input, and an operable create action via
  Compose semantics. TalkBack/device contrast and screen-reader execution
  remain external device evidence.
- [x] Local account-switch/activity-recreation coverage —
  `AccountSwitchPersistenceTest` verifies selected-pet isolation and session
  survival through activity recreation; `AccessibilityRegressionTest` covers
  primary semantics. True process death, uninstall/reinstall, and physical
  device execution remain external gates.

### Recommended remediation tasks
1. Build a per-domain cross-user authorization test suite (14 domains) — the single biggest gap.
2. Add real concurrency tests for credit reservation races and Premium grant races.
3. Wire `scripts/inspect_release_artifact.py` into CI; extend it beyond filename matching (inspect DEX/resources content, not just zip entry names).
4. Write Android accessibility regression tests and a process-death/reinstall/account-switch instrumentation matrix.
5. Expand `REQUIREMENTS_TRACEABILITY_MATRIX.md` from phase-range rows to per-requirement rows.

---

# Phase 17 — Release Engineering / Google Play Submission

- [x] `release/RC_MANIFEST.json` linkage — includes web-page hashes
- [x] Privacy policy exists as static HTML (`release/prod/web/privacy.html`) and account-deletion web resource (`release/prod/web/delete-account.html`) — Firebase Hosting is now configured to publish `release/prod/web`, with a structural regression; public HTTPS reachability and legal approval remain external.
- [x] `targetSdk=36` confirmed — `android/app/build.gradle.kts:9`
- [x] The five compliance worksheets exist and are populated with the shipped
  PETi data categories, safety boundaries, permissions, reviewer flow and
  external checklist. They remain source declarations requiring legal/Play
  Console submission and operator evidence; they do not declare out-of-scope
  collaboration, search or conversation features.
- [x] Play App Signing configuration docs — `release/PLAY_APP_SIGNING_CONFIGURATION.md` and `docs/runbooks/UPLOAD_KEY_RECOVERY.md` provide enrollment/configuration and recovery procedures; actual Play Console enrollment and key registration remain external gates.
- [x] `release/FINAL_GO_NO_GO.md` exists and is honest: "Go requires ... This implementation pass does not assert those external gates as passed."

### Recommended remediation tasks
1. Deploy `privacy.html`/`delete-account.html` to a real public HTTPS host and record the live URL — currently source files only, unconfirmed reachability.
2. [x] Source-side Play worksheets are complete enough for structured review; live wording/submission remains external.
3. [x] Remove out-of-scope data categories from `DATA_SAFETY_WORKSHEET.md`; the worksheet now states the 0–17 boundary explicitly.
4. [x] Add dedicated Play App Signing configuration and upload-key recovery documents.
5. Replace legal placeholder text in both web pages before any real submission.

---

# Scope Creep / Out-of-Spec Audit

**This is the single most consequential structural finding in the audit.** The canonical plan defines exactly 18 phases (0–17). Historical status text attributed substantial functionality to an invented numbering scheme — **"Phases 21–26"** and **"Phases 15–20"** — that does not exist anywhere in the approved plan; the current status document now explicitly labels that functionality out of scope.

### Confirmed out-of-scope `backend/app/` modules

| Module | Files | LOC | What it does | Wired into prod? |
|---|---:|---:|---|---|
| `future/` | 4 | 100 | God-object backing export/share/import, saved search, collections, assistant threads, caregiver invitations/memberships, automation rules/suggestions, care templates. Docstring literally says: *"Safe, deterministic foundations for Phases 21–26."* | **Registered; non-LOCAL routes are fail-closed** — `main.py`, backs ~55 routes in `api/v1.py:220-455` |
| `agents/` | 4 (2 src) | 356 | `AgentOrchestrator` — durable multi-step agent run/session state machine, action-approval workflow | **Registered; non-LOCAL routes are fail-closed** — `main.py`, dedicated router `api/agent_runs.py` (81 lines, 9 endpoints), also `api/v1.py:586-597` |
| `agent_runtime/` | 5 (5 src) | 94 | Budget guard, context broker, tool gateway, run-state machine, model-policy validator | Effectively dead — not actually consumed by `AgentOrchestrator.__init__` |
| `assistant/` | 2 (2 src) | 91 | `GroundedAssistant` — canned-text Q&A over search hits, hardcoded medical-keyword redirect | **Yes** — `main.py:297`, `api/v1.py:603` |
| `automation/` | 2 (2 src) | 73 | `RuleEngine` — deterministic trigger/action rules per pet | Instantiated but the standalone instance is **dead** — routes go through `future.*` instead |
| `care_advanced/` | 2 (2 src) | 100 | `CareRecordsService` — a **second, parallel, duplicate** care-record CRUD overlapping canonical Phase-6 `care` | **Yes** — `main.py:293`, `api/v1.py:552-566` |
| `collaboration/` | 2 (2 src) | 78 | Caregiver/viewer membership grants and authorization | **Yes** — `main.py:303`, `api/v1.py:610-617` |
| `economics/` | 2 (2 src) | 51 | `EconomicsPolicy` — a legacy cost/kill-switch/ledger boundary for AI ops | **Wired into `AnalysisService.process()` but parallel to the newer operations budget controls**; consolidation remains a local design gap |
| `portability/` | 2 (2 src) | 77 | A **second, independent** export/share/import implementation, parallel to `future`'s | **Yes** — `main.py:294`, `api/v1.py:571-581` |
| `search/` | 3 (2 src) | 88 | A **third, independent** search implementation, parallel to `future.search` | Instantiated but **dead** — no route calls it |
| `infrastructure/` | 1 | 24 | Firebase Admin factory | Legitimate glue, just an unspecified module name |

**Total: ~29 source files, ~1,130 LOC of backend logic outside the canonical domain list**, plus roughly half of `api/v1.py`'s 1,822 lines / 148 routes, plus the entire `api/agent_runs.py` router.

**Local test coverage:** dedicated suites now exist for `test_agent*`, `test_automation*`, `test_collaboration*`, `test_future*`, `test_portability*`, `test_search*`, `test_assistant*`, and `test_care_advanced*`. This proves repository contracts only; it does not promote these extensions into the canonical 0–17 release scope or provide external certification.

**Android side:** `android/features/{agents,automation,collaboration,pet-history-assistant,search}/` each contain only a `README.md` stub — scaffolding/namespace reservation, no Kotlin source, but confirms client-side intent to build the same out-of-scope surface.

### Invariant checks performed
- **No local AI models** in `agent_runtime`/`agents` — confirmed clean; `agent_runtime/release_policy.py` actually *enforces* `local_model_enabled=False`.
- **Dog-first guardrail/safety pipeline bypass check** — `assistant/grounding.py` never imports `app.ai`/`app.safety`; it's pure deterministic template text with a hardcoded keyword redirect. It doesn't bypass the real pipeline (it never touches it), but it **presents itself as an "AI assistant" over real pet data via a real authenticated endpoint while doing no actual grounded reasoning** — a misleading production surface.
- **Advertising/funding isolation** — `economics/`, `automation/`, `collaboration/` don't reference `credits`/`billing`/`advertising` directly; isolation appears intact but `economics` is dead code so this can't be fully assessed against real traffic.
- **Security concern**: `future.share()` embeds the raw share token directly alongside its digest in the stored/returned object — worth a security review if this ships.
- **Compliance worksheet corrected**: `release/DATA_SAFETY_WORKSHEET.md` now explicitly covers only the implemented PETi 0–17 surface and states that collaboration, search projections, conversations, and future assistant features are not declared as shipped functionality. Play Console review remains external.

### Recommended disposition
1. **Remove or consolidate:** the parallel `economics/` policy, standalone `automation.RuleEngine` instance (routes go through `future` instead), `agent_runtime/` (unused by `AgentOrchestrator`), and one of the three duplicate export/search implementations.
2. **Quarantine the wired-but-untested surface** (`future/`, `agents/`+`api/agent_runs.py`, `assistant/`, `care_advanced/`, `collaboration/`, `portability/`, `search/`) behind the fail-closed `is_out_of_scope_route` guard for non-LOCAL environments. Full route removal and a real scope decision remain required before Phase 16/17 certification.
3. **Formally re-scope**: if this functionality (caregiver sharing, assistant, automation, export/import) is genuinely wanted, write it up as canonical Phase 18+ (or amend Phases 1–17) with its own spec, guardrail integration, and test plan — not as a shadow plan riding along with zero tests.
4. **Correct `docs/ALL_PHASES_IMPLEMENTATION_STATUS.md` and `release/DATA_SAFETY_WORKSHEET.md`** immediately so they don't imply this work is part of an approved, certified plan — presenting unauthorized scope as certified progress is itself a compliance risk.

---

# Consolidated Critical-Path Action Plan

Work in this order — each tier blocks meaningful progress on the next.

## Tier 0 — Repository blockers
1. Completed locally: `./scripts/check.ps1` passes the current backend, Android, architecture, release, privacy, and infrastructure checks.
2. Completed locally: Premium trust boundaries, Dental guardrails, PETi Check safety precedence, and scope declarations are fail-closed and regression-tested.
3. Remaining external: perform the frozen-release provider, cloud, legal, device, and Play Console reviews.

## Tier 1 — Local safety/security status
4. Completed locally: mandatory Phase 4/5/9/10/11 safety tests, media checksum boundaries, atomic analysis claiming, and Body Check coverage pass.
5. Remaining external: run held-out/red-team provider suites and physical-device validation.

## Tier 2 — Local data-integrity status
6. Completed locally: RTDN canonical re-fetch, measurement foreign-key linkage, weekly-report timezone/status semantics, privacy residual inventories, and logging redaction tests.
7. Remaining external: execute residual-zero and race tests against deployed Firestore/GCS/Cloud Tasks.

## Tier 3 — Scope decision
8. Complete product-owner/legal approval of the Phase 18+ capability scope and keep all non-approved production routes fail-closed.

## Tier 4 — Release qualification
9. Build/sign/inspect the production AAB, execute Play Billing and RTDN lifecycle tests, complete accessibility and localization review, publish legal URLs, and obtain independent go/no-go approval.

