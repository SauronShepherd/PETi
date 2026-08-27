# PETi — Full Qualification, Test, Certification and 100% Implementation Build Plan

**Status:** Draft — not submitted; P0 repository baseline completed  
**Assessment date:** 2026-08-27  
**Repository:** `C:\Users\angel.alvarez\IdeaProjects\PETi`  
**Qualification target:** A production-ready PETi release for which every claimed feature is implemented, tested in its real execution environment, independently evidenced, legally/compliance reviewed, operationally ready, and approved for release.

## 1. Executive determination

PETi is **not yet fully qualified**. The repository contains substantial implementation and a strong local evidence framework, but its own release artifacts correctly classify the product as `SOURCE_READY_EXTERNAL_CERTIFICATION_PENDING` / `PASS_STATIC_ONLY`.

The remaining work is not one final coding task. It is a controlled completion program across:

1. one immediate repository test-collection defect;
2. real Firebase/GCP customer-path execution;
3. complete frozen-release Gemini and specialist certification;
4. physical-device, accessibility, media, FCM and deep-link verification;
5. privacy deletion/residual and operational failure drills;
6. Google Play billing, signing, declarations and submission evidence;
7. final traceability, independent review, go/no-go and rollback readiness.

The externally referenced planning documents listed in the request were not available at their supplied `C:\ANGEL\...` paths on this machine. This plan therefore uses the checked-out repository as the evidence source, especially `docs/PHASES_0_17_PENDING_CHECKLIST.md`, `docs/PHASES_0_17_CONTINUATION_STATUS.md`, `release/EXTERNAL_GATES.md`, `release/RC_BLOCKERS.md`, `release/REQUIREMENTS_TRACEABILITY_MATRIX.md`, the phase evidence contracts, and the implementation tree. The missing source documents must be supplied and reconciled before final sign-off.

## 2. Current evidence baseline

### 2.1 Evidence that exists

- Backend implementation, contracts, Android shell, infrastructure definitions, evaluation harnesses, release scripts and evidence manifests exist.
- Static release status is explicitly `PASS_STATIC_ONLY`.
- The current workspace now reports **451 backend tests passed**; older release evidence artifacts retain historical counts and are not silently rewritten because their hashes are part of the frozen source-artifact manifests.
- Android internal artifact, Android unit/lint checks, and API-35 emulator instrumentation evidence exist.
- Bounded sandbox evidence exists for Cloud Tasks/OIDC worker paths, Gemini PETi Check, specialist red-team smoke, and Weekly Report narration.
- Local test/evidence gates cover ownership, credits, media state, safety, billing abuse contracts, privacy primitives, logging, operations, and release-manifest integrity.

### 2.2 Current blockers and caveats

- The previously observed pytest collection failure is resolved: `scripts/__init__.py` was added and the canonical pytest path now includes the repository root.
- Release startup now rejects `MEMORY` storage in `STAGING` and `PRODUCTION`; only `LOCAL` and the explicitly supported DEV smoke configuration may use ephemeral storage.
- Phase 20D care records now accept the existing Firestore persistence adapter, hydrate across process restarts, and persist soft deletion; advanced non-local routes remain disabled pending full phase certification.
- Phase 22 collaboration memberships now accept the existing Firestore persistence adapter, hydrate across process restarts, persist revocation, and retain pet-scoped authorization boundaries; non-local routes remain disabled pending full phase certification.
- Phase 23 deterministic automation rules now accept the existing Firestore persistence adapter, hydrate across process restarts, and persist `last_fired_key` so duplicate event evaluation remains idempotent; non-local routes remain disabled pending full phase certification.
- Phase 20D care records now support owner-scoped updates with payload validation, immutable record identity/type, durable `updated_at`, and soft-delete protection; the update route remains disabled outside LOCAL pending phase certification.
- Phase 20D care-record create/read validation is now centralized: malformed payloads are rejected, longitudinal bundles require an owned pet, and cross-user list reads remain empty rather than revealing resource existence.
- Phase 24 personal pet memory now supports durable storage, restart hydration, source invalidation, version increments and persistence of invalidation state; public search/memory routes remain disabled outside LOCAL pending full source-grounded certification.
- Phase 25 grounded answers now enforce a 500-character question limit, pet-scoped citation filtering, non-empty citation identity, duplicate suppression and bounded excerpts; public assistant routes remain disabled outside LOCAL pending full source-grounded certification.
- The pending Phase 17 checklist was reconciled after the hosting implementation: privacy and account-deletion source pages exist locally and are configured for Firebase Hosting; only public HTTPS reachability and legal approval remain pending.
- Phase 21 share-token handling now stores only SHA-256 digests in both portability paths; raw tokens are returned only in the immediate creation response and are covered by security regression tests.
- Phase 21 portability share grants now persist and hydrate through Firestore, including revocation state; share routes remain disabled outside LOCAL pending full interoperability/privacy certification.
- Portability now exposes a fail-closed share resolver that verifies the digest, expiry and revocation state before granting access.
- Portability exports now include a deterministic SHA-256 content hash; import preview validates the hash and rejects tampered packages.
- Portability share creation, revocation, export timestamps and resolution now use an injectable clock, making expiry boundary behavior deterministic and certification-testable.
- Phase 22 invitation handling now persists only token digests, returns raw tokens only at creation, performs hashed acceptance lookup, validates roles and is covered by security regression tests.
- Phase 22 invitations now carry a bounded durable TTL (1–168 hours) and expired invitations are rejected during hashed acceptance lookup.
- Invitation creation now requires a non-empty invitee, distinguishes invalid role/TTL errors, and acceptance durably transitions the invitation to `ACCEPTED`, preventing replay.
- A repository token sweep found no remaining raw share/invitation token persistence in the hardened paths; logging, privacy-export, scope-guard and release-manifest checks remain passing.
- Privacy export/deletion orchestration now includes the newly persisted advanced care, collaboration, future-domain and portability-share stores; the bindings are wired after service initialization and remain subject to live residual verification.
- Collaboration privacy now covers both ownership directions: owner accounts export/revoke their grants, and caregiver accounts export/revoke memberships where they are the member.
- Account-deletion job state and idempotency now persist through the existing Firestore adapter and hydrate after restart; residual verification remains fail-closed.
- Account deletion now performs an owner-scoped orphan sweep after pet traversal, so imported or legacy records, analyses, reports and media without a live-pet foreign key cannot survive solely because their parent pet is missing; regression coverage is included.
- Residual verification now independently counts live advanced care records, collaboration memberships in either owner/member direction, future-domain items and portability share grants.
- Added an end-to-end local API regression proving the request correlation ID reaches analysis-job creation; distributed Cloud Tasks/log export verification remains external.
- Live production GCP/Firebase topology, IAM, Firestore, GCS, Cloud Tasks, Scheduler, Secret Manager and monitoring evidence is incomplete.
- The active bounded sandbox observation recorded `PETI_STORAGE_MODE=MEMORY` in at least one deployment observation; this cannot qualify persistent production behavior.
- Customer-authenticated product-path smoke is incomplete.
- Full specialist certification is incomplete for Initial Scan, Dental, Feces and Body Check.
- Real Firestore contention/transaction evidence, live GCS checksum/privacy evidence, and deletion-race residual evidence are incomplete.
- Physical-device, accessibility/TalkBack, camera, picker, microphone, notification and Android recovery evidence is incomplete.
- Real Google Play product, purchase, RTDN, license-tester and renewal/failure lifecycle evidence is incomplete.
- Production signing, artifact custody, public HTTPS/legal pages, Play forms, pre-launch report and external reviewer access are incomplete.
- Source-side placeholders and fail-closed `PENDING` release flags are expected until external certificates exist; they must not be silently converted to `PASS`.
- `pass`/`NotImplemented` occurrences must be classified: some are intentional no-op exception handling or abstract boundaries, while others may be unfinished implementation. Each must be reviewed and covered by an explicit test or documented rationale.

## 3. Non-negotiable qualification policy

No gate may be marked complete because code exists, a unit test passes, a source manifest is generated, or a synthetic fixture succeeds. A gate is complete only when:

1. the exact release commit/configuration is frozen;
2. the test is executed in the environment named by the requirement;
3. inputs are privacy-safe and reproducible;
4. raw secrets/tokens/PII are excluded from evidence;
5. an artifact records version, timestamp, environment, configuration/model IDs, result, limitations and SHA-256;
6. an independent reviewer accepts the artifact;
7. the traceability matrix links requirement → implementation → test → evidence → approval.

## 4. Workstream P0 — restore a green repository baseline

### P0.1 Fix test collection and import boundaries — **complete**

- Reproduce the failure from repository root and from `backend`.
- Decide whether `scripts` is intended to be an importable package or whether the test should import through an approved package path.
- Add the minimal package/configuration correction; do not duplicate production code into tests.
- Add a regression test for the import path and run collection from the documented commands.
- Run `pytest --collect-only -q`, then the full backend suite.
- Record Python version, dependency lock state, command, count and result in a new evidence artifact.

**Result:** `pytest -q backend/tests` completes with **451 passed**; the import path is covered by `backend/tests/test_provision_user_role.py` and release-manifest/media-retention/reward-integrity is covered by the corresponding regression suites.

### P0.2 Reconcile test-count drift — **complete**

- Compare the historical 255/266/293/297/303/304/305 counts with current collection.
- Identify newly added, skipped, deselected and environment-dependent tests.
- Make the canonical test command explicit in `README.md` and release evidence.
- `scripts/check.ps1` now selects Android Studio's Java 17+ runtime when the host default is Java 11; its backend/static stages pass and Android verification can proceed on hosts with that bundled JBR.
- Release evidence must continue to record the executed count for every RC run.

### P0.4 Static gate verification — **complete for repository scope**

- `python -m ruff check backend`: passed.
- `python -m mypy backend/app`: passed for 135 source files.
- `python -m pytest -q backend/tests`: **451 passed**.
- `scripts/check.ps1`: **passed end-to-end locally** after hardening JDK selection. This included backend/static gates, Android `test lint assembleDebug`, security/evaluation checks, release evidence checks, and Terraform initialization/validation. `assembleRelease` remains intentionally skipped because AdMob release inputs are external.
- `scripts/release_gate_check.py`: `PASS_STATIC_ONLY`.
- `scripts/check_traceability.py`: `PASS_SOURCE_LEVEL`.
- The requirements traceability matrix now contains 27 explicit rows, including domain-level privacy, credential, portability, billing, assistant, durable-care, and release-evidence controls; external execution and approval remain explicitly separated.
- `scripts/build_release_evidence.py` now regenerates the same 27-row domain-level traceability matrix, preventing an evidence rebuild from silently reverting it to the former phase-only 18-row matrix.
- `scripts/check_scope_guard.py`: `PASS_FAIL_CLOSED_NON_LOCAL`.
- `scripts/check_release_manifests.py`: `PASS_FAIL_CLOSED_EXTERNAL_GATES_EXPLICIT`.
- `scripts/test-floci-phase8-11.ps1`: local specialist acceptance passed (`17` backend regression tests plus `2/2` fixture cases); this is bounded local evidence and does not clear real Gemini, device, or independent certificate gates.
- These results do not clear external provider, Play, physical-device, production or legal gates.

### P0.5 Prevent ephemeral release environments — **complete for repository scope**

- `Settings.validate_startup()` now rejects `PETI_STORAGE_MODE=MEMORY` for `STAGING` and `PRODUCTION`.
- Added regression coverage for both release environments.
- Existing DEV smoke behavior remains available, but it is not evidence of durable release readiness.

### P0.3 Classify incomplete-looking code

- Review every `pass`, `NotImplementedError`, placeholder, in-memory store and `PENDING` release flag under `backend/`, `android/`, `infra/`, `scripts/` and `release/`.
- For each item, label `implemented`, `intentional abstraction`, `test-only fake`, `fail-closed pending gate`, or `unfinished`.
- Implement unfinished items or add an explicit feature exclusion and release guard.
- Add tests proving that all excluded/future paths fail safely and cannot be exposed by production flags.

## 5. Workstream P1 — freeze scope and source traceability

- Obtain all 22 externally referenced planning/specification files and hash them.
- Reconcile them against `docs/specs/`, `product/`, `docs/PHASES_0_17_PENDING_CHECKLIST.md`, and all Phase 20A–25 evidence contracts.
- Build a requirements inventory with stable IDs for functional, non-functional, safety, privacy, data, UI, infrastructure, AI, billing and release requirements.
- Extend `release/REQUIREMENTS_TRACEABILITY_MATRIX.md` to include every Phase 0–25 requirement and every claimed UI/API/worker capability.
- Mark each requirement `implemented`, `locally tested`, `sandbox tested`, `staging tested`, `production certified`, or `not in release scope`.
- Ensure every unchecked requirement has an owner, dependency, test procedure, evidence path and exit criterion.
- Freeze the release branch, dependency versions, prompt versions, schema versions, model IDs, feature flags, cost profiles and infrastructure plan.

**Exit:** no unowned requirement, no unclassified document conflict, and one immutable RC configuration exists.

## 6. Workstream P2 — real sandbox/staging product path

### P2.1 Provision and validate cloud topology

- Provision a dedicated non-production Firebase/GCP project using Terraform.
- Verify Cloud Run API and worker services, service accounts, least-privilege IAM, Cloud Tasks OIDC, Scheduler, Firestore indexes/rules, private GCS buckets, Secret Manager, Pub/Sub/RTDN plumbing and monitoring.
- Replace placeholder Firebase configuration only through environment provisioning; never commit secrets.
- Confirm API and worker use durable Firestore/GCS modes, not memory fallbacks.
- Run deployment/preflight scripts and archive Terraform plan/apply outputs, IAM bindings, endpoint revisions and configuration snapshot.
- Execute negative checks: customer token to worker, worker token to public API, cross-project resource access, unauthenticated private bucket access, missing secret, revoked service account and disabled provider.

### P2.2 Execute customer-authenticated vertical slices

For at least two independent users and multiple pets:

- sign-up/sign-in/sign-out/account switch;
- pet creation, edit, deletion and ownership isolation;
- media picker/camera/audio upload, checksum, finalize, retry, cancel and resume;
- analysis submission, duplicate delivery, status polling, cancellation and result hydration;
- care records and candidate review/writeback;
- specialist request/result/review;
- weekly report generation, delivery and deep-link opening;
- export, deletion request, tombstone behavior and re-login denial;
- notification permission and delivery behavior.

Capture request correlation IDs and sanitized durable state, never raw media, tokens or provider payloads.

### P2.3 Data and concurrency verification

- Firestore transaction contention for credits and analysis claims.
- Duplicate Cloud Tasks delivery and retry-after-timeout.
- Cross-user/cross-pet reads and writes.
- Account switch while requests are in flight.
- Upload finalize races, checksum mismatch, expired upload and orphan cleanup.
- Deletion racing with queued analysis, notification, report, specialist and maintenance work.
- Restart/redeploy workers and verify state recovery.

**Exit:** complete customer path passes with durable stores, correct IAM, repeatable evidence and zero cross-tenant findings.

## 7. Workstream P3 — AI/provider and safety certification

### P3.1 Freeze provider configuration

- Record exact Vertex project/location, model ID, SDK version, safety settings, system prompts, schema versions, provider flags, budget/cost profile and code commit.
- Ensure evidence records usage/cost metadata without sensitive prompt or source data.
- Verify kill switches and spend limits fail closed across multiple service instances.

### P3.2 PETi Check

- Rerun dev, held-out, red-team and regression suites against the frozen RC.
- Verify uncertainty, evidence quality, limitations, red flags, safety precedence, unsupported claims, prompt injection and untrusted media/text handling.
- Reconcile the JSON result, evidence-quality gates and release decision.
- Obtain an independent PETi Check certificate.

### P3.3 Specialists

For Dog Initial Scan, Dental, Feces and Body Check:

- execute complete dev/held-out/red-team/regression matrices against real Gemini;
- include non-dog/species mismatch, low-quality media, adversarial text, prohibited clinical language, uncertainty and escalation cases;
- verify specialist capability flags, profile writeback, human review states and no unauthorized cross-specialist writes;
- record model/config/cost/latency/schema validation and red-team findings;
- produce independently reviewed release certificates and bind their IDs to release flags.

### P3.4 Weekly Report and history assistant

- Re-run deterministic four-split report tests and frozen-RC narration evaluation.
- Execute real Scheduler duplicate, retry, week-boundary and DST scenarios.
- Verify source grouping, citation/provenance, no invented events, safety copy, delivery, notification privacy and Android deep links.
- For Phase 24 search/memory, verify source-first indexing, authorization, query limits, invalidation, projection deletion and no unbounded narrative memory.
- For Phase 25 assistant, verify source-grounded answers, citation validator, refusal/uncertainty behavior, search authorization, funding policy, prompt binding and red-team suite.
- Produce the report release decision and Pet History Assistant certificate only after independent review.

## 8. Workstream P4 — records, care workflows and collaboration

- Validate Phase 20D care-record schemas, provenance, privacy classification, non-prescriptive wording, reminders, exports and deletion dependencies.
- Execute longitudinal timeline tests: edits, corrections, duplicate events, out-of-order dates, timezone/DST, pet merge/account switch and deleted sources.
- Validate Phase 21 export/import: schema version, manifest integrity, provenance, scope, expiry, revocation, preview, duplicate policy and audit trail.
- Validate Phase 22 household collaboration: pet-scoped roles, invitations, expiry, revocation, caregiver privacy, billing separation, account switching and deleted-owner behavior.
- Validate Phase 23 automation: deterministic rules, thresholds, idempotency, quiet hours, notification privacy, no clinical inference, revocation and deletion.
- Execute Android UI flows for all states: loading, empty, error, offline/retry, pending review, denied permission and partially completed workflow.

## 9. Workstream P5 — privacy, security and compliance qualification

- Obtain legal-approved privacy policy, controller identity, jurisdiction, contact address, effective date and deletion instructions.
- Verify public HTTPS privacy and deletion URLs, TLS, redirects, caching, availability and response content.
- Execute account deletion against durable Firestore/GCS/queues/indexes/logs/exports/notifications/provider references.
- Verify tombstone prevents rehydration and queued work cannot recreate data.
- Run deletion concurrently with uploads, worker retries, reports, specialists, reminders and exports.
- Perform post-deletion residual sweeps using independent credentials and provider/bucket/index queries.
- Verify export contains only authorized data and has a coverage/provenance manifest.
- Run dependency vulnerability, secret, artifact, IAM, rules, storage, transport, logging-redaction and abuse testing.
- Complete Data Safety, Health Apps, permissions, privacy and child/sensitive-data declarations with legal review.

## 10. Workstream P6 — Android device and accessibility certification

Test the signed candidate on a documented matrix of supported API levels, screen sizes and at least one physical device per critical capability:

- sign-in/account switch and offline transitions;
- camera photo/video capture, picker, URI permissions and rotation/process death;
- microphone/audio capture, cancellation and cleanup;
- upload resume after network loss, app kill and reboot;
- notification permission, channel behavior, tap/deep-link and duplicate notification;
- loading, empty, error, retry and accessibility states;
- TalkBack traversal, labels, focus order, contrast, touch targets, dynamic font and reduced motion;
- battery/network constrained behavior and crash recovery.

Archive device model/API/build hash, test video/screenshots where appropriate, defect IDs and final accessibility sign-off.

## 11. Workstream P7 — billing and monetization readiness

Even if the initial free release excludes premium billing, the release must prove the dormant boundary cannot accidentally activate.

If billing is in scope:

- configure real Play products and license testers;
- execute purchase, pending, approval, decline, acknowledgement, duplicate, restore, renewal, grace, hold, recovery, cancellation and involuntary churn;
- deliver real RTDN through Pub/Sub and verify signature/trust, owner resolution, replay safety and reconciliation;
- verify allowance/entitlement state under retries, account switch and deletion;
- prove no raw purchase token appears in logs/evidence.

If billing is out of scope:

- keep production flags disabled;
- run the dormant-boundary and forged-input tests;
- document the explicit product scope and deferred certification in the release decision.

## 12. Workstream P8 — operations, SLOs and disaster recovery

- Define and approve SLOs for API availability/latency, worker completion, queue age, report delivery, deletion completion and provider error rate.
- Configure bounded-cardinality metrics, redacted structured logs, traces/correlation IDs, alerts and dashboards.
- Execute real drills for provider outage, queue backlog, GCS failure, Firestore contention, billing outage, reward/SSV failure, notification failure and deletion residual.
- Verify kill switches, emergency cost controls, retry ceilings, dead-letter handling, reconciliation and operator audit trails.
- Test backup/restore or documented recovery boundaries, rollback to prior Cloud Run revision, schema compatibility and mobile rollback strategy.
- Validate support runbook, incident severity, escalation, customer communication and evidence retention.

## 13. Workstream P9 — release artifact, production and Play gates

- Create production Firebase/GCP project and least-privilege accounts.
- Bind production secrets through Secret Manager and validate production config snapshot.
- Build signed AAB with production-safe variant and upload-key custody record.
- Run forbidden-artifact inspection for Gemini keys, service-account JSON, local AI models, debug bypasses, test routes, fake providers and placeholder credentials.
- Verify package ID, version code/name, min/target SDK, permissions, network security, backup policy and Play integrity settings.
- Publish legal web resources over HTTPS and verify deletion endpoint behavior.
- Complete store listing, screenshots, content rating, Data Safety, Health Apps and permissions declarations.
- Upload to Play internal track, execute reviewer instructions using a non-admin test persona, collect pre-launch report, resolve blockers and preserve submission evidence.
- Verify rollback package, release notes, incident contact, support channel and artifact hashes.

## 14. Evidence and certification package

For every gate, create a sanitized artifact containing:

- requirement IDs and test case IDs;
- commit, release version, configuration and environment;
- timestamp/timezone and operator or reviewer;
- inputs/corpus version and privacy classification;
- command/procedure and result;
- metrics, latency, cost and failure details where applicable;
- limitations and residual risk;
- artifact SHA-256 and retention location;
- independent reviewer approval.

Refresh, only after artifacts are complete:

- `release/EVIDENCE_MANIFEST.json`;
- `release/RC_MANIFEST.json`;
- `release/REQUIREMENTS_TRACEABILITY_MATRIX.md`;
- `release/PHASE16_CERTIFICATION_REPORT.md`;
- phase 11–25 evidence/certificate/decision files;
- `release/RC_BLOCKERS.md`;
- `release/FINAL_GO_NO_GO.md`.

## 15. Dependency-ordered execution sequence

1. Fix P0 test collection and establish a reproducible green baseline.
2. Obtain and reconcile the missing external planning documents.
3. Freeze requirements, RC source, prompts, schemas, models, flags and infrastructure.
4. Provision durable sandbox/staging and clear IAM/configuration blockers.
5. Execute authenticated product vertical slices and persistence/concurrency tests.
6. Run complete AI/provider and specialist matrices against the frozen RC.
7. Run records, collaboration, automation, search, memory and assistant certification.
8. Execute privacy deletion/residual, security, accessibility and physical-device tests.
9. Execute operations/SLO/failure/recovery drills.
10. Execute Play billing or formally exclude it from this release with fail-closed evidence.
11. Build/sign/inspect the production candidate and complete legal/Play declarations.
12. Obtain independent certification and reviewer access.
13. Rebuild evidence manifests and traceability hashes.
14. Clear every P0/P1 blocker; approve final go/no-go; submit only after explicit authorization.

## 16. Final definition of done

PETi may be marked fully qualified only when all of the following are true:

- repository tests collect and pass from the documented clean environment;
- no required feature is represented only by a stub, placeholder, memory fallback or synthetic-only path;
- every requirement is traced to implementation, executed test and accepted evidence;
- all live cloud, provider, persistence, IAM, deletion and concurrency gates pass;
- all AI and specialist certificates bind to one frozen RC;
- physical-device and accessibility matrices pass;
- privacy, security, legal and store declarations are approved;
- operational drills, SLOs, monitoring, rollback and support readiness pass;
- signed artifact inspection passes and hashes are recorded;
- Play internal-track/reviewer/pre-launch gates pass, or billing/Play is explicitly out of scope and fail-closed;
- `release/RC_BLOCKERS.md` is empty or contains only explicitly accepted non-release risks;
- `release/FINAL_GO_NO_GO.md` is signed by the accountable owner;
- no document or evidence artifact claims production certification beyond what was actually executed.

Until then, the correct status remains **not fully qualified; implementation substantially present, external certification pending**.

## 17. Initial task register

| ID | Priority | Task | Owner | Depends on | Evidence / exit |
|---|---:|---|---|---|---|
| P0-001 | P0 | Fix `scripts.provision_user_role` test import and restore collection | Engineering | — | **Complete:** full pytest collection/pass; current suite 451 passed |
| P0-002 | P0 | Reconcile current vs historical test counts | QA | P0-001 | **Complete for local baseline:** canonical root run passes 451 tests; frozen historical evidence remains unchanged |
| P0-003 | P0 | Prevent ephemeral release environments | Platform | — | **Complete for repository scope:** STAGING/PRODUCTION reject `MEMORY` |
| P1-001 | P0 | Obtain/hash/reconcile all missing source documents | Product/Engineering | — | Requirements inventory |
| P1-002 | P0 | Freeze RC config, prompts, schemas, model and flags | Release | P1-001 | Immutable RC manifest |
| P2-001 | P0 | Provision durable staging GCP/Firebase topology | Platform | P1-002 | IAM/topology/apply evidence |
| P2-002 | P0 | Execute authenticated end-to-end product matrix | QA/Platform | P2-001 | Customer-path evidence |
| P2-003 | P0 | Run Firestore/GCS/queue race and residual tests | Backend/Privacy | P2-002 | Race/residual certificate |
| P3-001 | P0 | Run frozen-RC PETi Check certification | AI Safety | P1-002/P2-001 | Independent certificate |
| P3-002 | P0 | Run all four specialist certification suites | AI Safety | P3-001 | Four certificates |
| P3-003 | P1 | Certify report, search, memory and assistant | AI/Product | P1-002/P2-002 | Decisions/certificates |
| P4-001 | P1 | Certify records/collaboration/automation longitudinal behavior | Product/QA | P2-002 | Phase 20D persistence implementation improved; full Phase 20D–23 evidence remains pending |
| P4-002 | P1 | Persist collaboration memberships and revocations | Backend | P2-001 | **Complete for repository scope:** Firestore wiring plus restart/authorization tests |
| P4-003 | P1 | Persist automation rules and evaluation idempotency | Backend | P2-001 | **Complete for repository scope:** Firestore wiring plus restart/replay tests |
| P4-004 | P1 | Add owner-scoped care-record updates | Backend | P4-001 | **Complete for repository scope:** service/API validation and tests |
| P4-005 | P1 | Harden care-record payload and read-boundary validation | Backend | P4-004 | **Complete for repository scope:** validation and privacy regression tests |
| P4-006 | P1 | Persist personal pet memory and source invalidation | Backend | P2-001 | **Complete for repository scope:** durable adapter and restart/invalidation test |
| P4-007 | P1 | Harden grounded assistant input and citation boundaries | Backend | P4-006 | **Complete for repository scope:** bounded input and citation-filter tests |
| P4-008 | P0 | Remove raw share tokens from durable payloads | Security/Backend | P2-001 | **Complete for repository scope:** digest-only persistence tests |
| P4-009 | P1 | Persist portability share grants and revocations | Backend | P4-008 | **Complete for repository scope:** Firestore wiring plus restart/revocation test |
| P4-010 | P0 | Remove raw caregiver invitation tokens from durable payloads | Security/Backend | P4-009 | **Complete for repository scope:** digest-only invitation acceptance test |
| P4-011 | P1 | Enforce caregiver invitation expiry | Backend | P4-010 | **Complete for repository scope:** bounded TTL and expired-token test |
| P4-012 | P0 | Make invitation acceptance single-use and validate invitee/TTL | Backend/Security | P4-011 | **Complete for repository scope:** durable consume and replay-prevention tests |
| P4-013 | P0 | Verify portability shares before access | Security/Backend | P4-009 | **Complete for repository scope:** token, expiry and revocation tests |
| P4-014 | P1 | Add portable-package integrity manifest and import validation | Backend/Security | P4-013 | **Complete for repository scope:** deterministic hash and tamper test |
| P4-015 | P1 | Make portability expiry/revocation time deterministic | Backend/QA | P4-014 | **Complete for repository scope:** injectable-clock expiry test |
| P4-016 | P1 | Verify correlation ID propagation into analysis creation | Observability/Backend | P2-002 | **Complete for repository scope:** API propagation test |
| P4-017 | P0 | Include Phase 20D–24 stores in privacy export/deletion | Privacy/Backend | P2-003 | **Complete for repository scope:** orchestration wiring; live residual evidence pending |
| P4-018 | P0 | Cover caregiver-side membership export and revocation | Privacy/Security | P4-017 | **Complete for repository scope:** owner/member privacy regression test |
| P4-019 | P0 | Persist account-deletion job state and idempotency | Privacy/Backend | P4-017 | **Complete for repository scope:** restart/replay test; live deletion residual evidence pending |
| P4-020 | P0 | Inventory Phase 20D–24 domains during deletion verification | Privacy/Security | P4-019 | **Complete for repository scope:** new-domain residual test; live store evidence pending |
| P4-021 | P1 | Preserve personal-memory timestamps across durable-store restart | Backend/QA | P4-006 | **Complete for repository scope:** ISO timestamp hydration and injectable-clock regression test |
| P4-022 | P1 | Preserve weekly-report timestamps across durable-store restart | Backend/QA | P4-001 | **Complete for repository scope:** serialized timestamp hydration and regression test |
| P4-023 | P1 | Activate canonical search service at the authenticated search endpoint | Backend/QA | P3-003 | **Complete for repository scope:** route wiring, filtering/limit hardening, and contract tests |
| P4-024 | P0 | Remove share-token digests from public response payloads | Security/Backend | P4-008 | **Complete for repository scope:** response redaction and persistence-security regression test |
| P4-025 | P0 | Remove caregiver-invitation digests from public response payloads | Security/Backend | P4-010 | **Complete for repository scope:** response redaction and invitation-security regression test |
| P4-026 | P0 | Centralize future-domain token redaction in public serialization | Security/Backend | P4-024/P4-025 | **Complete for repository scope:** serializer-level digest/raw-token redaction and regression coverage |
| P4-027 | P1 | Preserve future-domain lifecycle timestamps across durable-store restart | Backend/QA | P4-009 | **Complete for repository scope:** serialized timestamp hydration and restart regression test |
| P4-028 | P1 | Preserve agent-session/run lifecycle timestamps across durable-store restart | Backend/QA | P4-003 | **Complete for repository scope:** serialized timestamp hydration and restart regression test |
| P4-029 | P1 | Preserve specialist-analysis timestamps across durable-store restart | Backend/QA | P3-002 | **Complete for repository scope:** serialized timestamp hydration and queued-analysis regression test |
| P4-030 | P1 | Preserve premium-entitlement timestamps across durable-store restart | Billing/QA | P7-001 | **Complete for repository scope:** serialized timestamp hydration and entitlement regression test |
| P4-031 | P1 | Make collaboration expiry checks deterministic | Backend/QA | P4-002 | **Complete for repository scope:** injectable clock and expiry-boundary regression test |
| P4-032 | P0 | Wire personal-memory persistence into startup and privacy export/deletion | Privacy/Backend | P4-006 | **Complete for repository scope:** main service wiring, canonical export domain, deletion adapter, and regression coverage |
| P4-033 | P0 | Prove personal-memory owner deletion removes durable rows | Privacy/QA | P4-032 | **Complete for repository scope:** backing-store deletion regression test |
| P4-034 | P1 | Expose persisted personal memories through the authenticated pet-memory API | Backend/API | P4-032 | **Complete for repository scope:** owner/pet-scoped response field and service-level isolation coverage |
| P4-035 | P0 | Normalize Phase 6 timestamps during durable-store hydration | Backend/QA | P2-003 | **Complete for repository scope:** measurements, care, occurrence, device, notification timestamp coercion and restart regression coverage |
| P4-036 | P0 | Normalize records-vault timestamps during durable-store hydration | Backend/QA | P2-003 | **Complete for repository scope:** document, candidate, and documented-fact timestamp coercion and restart regression coverage |
| P4-037 | P0 | Preserve partial source dates during records hydration | Backend/QA | P4-036 | **Complete for repository scope:** lifecycle-only coercion and `YYYY-MM` candidate-date regression coverage |
| P4-038 | P0 | Normalize media asset/session timestamps during metadata hydration | Media/QA | P2-003 | **Complete for repository scope:** asset and upload-session timestamp coercion and restart regression coverage |
| P4-039 | P0 | Hydrate Initial Scan candidates and review audit records after restart | Specialist/QA | P3-002 | **Complete for repository scope:** separate collection hydration, timestamp normalization, and pending-review regression coverage |
| P4-040 | P0 | Make Phase 6 hydration fail closed per malformed row | Backend/QA | P4-035 | **Complete for repository scope:** invalid timestamp/shape isolation and mixed-row startup regression coverage |
| P4-041 | P0 | Verify release-manifest artifact existence and hashes fail closed | Release/Security | P1-002 | **Complete for repository scope:** checker validates repository containment, existence, and SHA-256; builder excludes self-referential phase-17 manifest; regression coverage added |
| P4-042 | P0 | Make the canonical gate hash generated evidence after all evidence builders run | Release/QA | P4-041 | **Complete for repository scope:** specialist inventory generation now precedes release-manifest hashing in PowerShell and POSIX gates; full gate passes with manifest integrity enabled |
| P4-043 | P1 | Prevent media-retention API from converting unexpected server errors into client errors | API/Security | P4-042 | **Complete for repository scope:** retention endpoint maps only domain/value errors to HTTP 400; regression covers invalid retention class |
| P4-044 | P1 | Audit authenticated API handlers for broad exception-to-client-error conversions | API/Security | P4-043 | **Complete for repository scope:** no broad API handler catch remains; unexpected failures use server-error handling while domain errors retain explicit mappings |
| P4-045 | P1 | Make media retention policy timing deterministic | Media/QA | P4-044 | **Complete for repository scope:** retention policy and cleanup accept an injectable clock; exact-expiry regression coverage added |
| P4-046 | P1 | Persist media retention-class changes and recalculated deadlines | Media/Backend | P4-045 | **Complete for repository scope:** retention changes now write the updated asset through the metadata adapter; durable-save regression coverage added |
| P4-047 | P0 | Persist terminal media expiry state after retention cleanup | Media/Privacy | P4-046 | **Complete for repository scope:** due-asset expiry now persists `EXPIRED`/`deleted_at` after object deletion; restart-state regression coverage added |
| P4-048 | P1 | Make rewarded-ad intent creation and expiry checks deterministic | Billing/QA | P4-047 | **Complete for repository scope:** reward lifecycle accepts an injectable clock and exact expiry-boundary regression coverage prevents timing drift |
| P4-049 | P0 | Make rewarded-ad callback verification atomic under duplicate delivery | Billing/Security | P4-048 | **Complete for repository scope:** Google callback verification is serialized under the reward lock; concurrent duplicate-delivery regression proves one grant |
| P4-050 | P1 | Make credit lifecycle timestamps deterministic | Billing/QA | P4-049 | **Complete for repository scope:** credit expiry, quote, reservation, consume, and release paths accept an injectable clock; expiry regression coverage added |
| P4-051 | P0 | Persist expired reservation terminal state after timeout release | Billing/Privacy | P4-050 | **Complete for repository scope:** timeout expiry persists final `EXPIRED` status after releasing funds; restart regression coverage added |
| P4-052 | P0 | Serialize nested credit-domain values before durable persistence | Billing/Backend | P4-051 | **Complete for repository scope:** dataclasses, enums, mappings, and collections are normalized before adapter writes; reservation restart regression proves hydration remains lossless |
| P4-053 | P1 | Normalize credit lifecycle timestamps during durable hydration | Billing/QA | P4-052 | **Complete for repository scope:** grant, reservation, and ledger ISO timestamps are coerced on restart; serialized-hydration regression coverage added |
| P4-054 | P0 | Persist rewarded-ad intents and provider transaction replay markers | Billing/Security | P4-053 | **Complete for repository scope:** reward intents and transaction IDs hydrate/save through the economic store; restart persistence regression added |
| P4-055 | P1 | Persist expired status from the legacy rewarded callback path | Billing/QA | P4-054 | **Complete for repository scope:** expired callback intents transition and persist as `EXPIRED`; terminal-state regression added |
| P4-056 | P0 | Prove rewarded-ad replay protection survives service restart | Billing/Security | P4-055 | **Complete for repository scope:** regression grants a callback, restarts the reward service, and verifies the persisted transaction marker rejects replay |
| P4-057 | P1 | Persist invalid state for malformed rewarded-ad amounts | Billing/Security | P4-056 | **Complete for repository scope:** malformed reward amounts now transition and persist the intent as `INVALID`; regression coverage added |
| P4-058 | P1 | Make privacy export/deletion timestamps deterministic | Privacy/QA | P4-057 | **Complete for repository scope:** export, tombstone, deletion, and completion timestamps use an injectable clock; deterministic completion regression added |
| P4-059 | P0 | Redact Google Play purchase tokens from public entitlement responses | Billing/Security | P4-058 | **Complete for repository scope:** premium public serialization removes raw purchase tokens; response-redaction regression added |
| P4-060 | P0 | Fail closed for premium reads after entitlement deadline | Billing/Security | P4-059 | **Complete for repository scope:** `PremiumService.current()` downgrades expired entitlement reads to `FREE` using the injected clock; deadline regression added |
| P4-061 | P1 | Make agent state-transition timestamps deterministic | Agents/QA | P4-060 | **Complete for repository scope:** `AgentOrchestrator` accepts an injectable clock for run-state transitions; timestamp regression added |
| P4-062 | P1 | Make media upload/finalization/deletion timestamps deterministic | Media/QA | P4-061 | **Complete for repository scope:** `MediaService` accepts an injectable clock for authorization expiry and lifecycle timestamps; regression coverage added |
| P4-063 | P1 | Make advanced-care mutation timestamps deterministic | Care/QA | P4-062 | **Complete for repository scope:** advanced-care update/delete timestamps use an injectable clock; mutation regression added |
| P4-064 | P0 | Bind rewarded callbacks to supported providers | Billing/Security | P4-063 | **Complete for repository scope:** unsupported providers are rejected and callback verification requires an exact intent-provider match before granting credits |
| P4-065 | P0 | Delete owner-scoped orphan rows not attached to a live pet | Privacy/Backend | P4-064 | **Complete for repository scope:** account deletion sweeps records, analyses, reports, and media after pet traversal so legacy/imported orphan rows cannot survive solely because their pet foreign key is missing; regression coverage added |
| P4-066 | P0 | Purge Phase 6 care graph during account deletion | Privacy/Backend | P4-065 | **Complete for repository scope:** Phase 6 now removes owner measurements, care items, occurrences, and notification preferences from memory and durable storage; regression coverage added |
| P4-067 | P0 | Include Phase 6 measurement domain in canonical deletion plan | Privacy/Backend | P4-066 | **Complete for repository scope:** dependency resolver now carries `measurements` in the executable plan, and canonical deletion execution is regression-tested; manifest hashes rebuilt |
| P4-068 | P0 | Remove Phase 6 idempotency state during account deletion | Privacy/Security | P4-067 | **Complete for repository scope:** owner-scoped in-memory and hashed durable idempotency entries are purged with the care graph, preventing post-deletion retries from dereferencing or replaying deleted state; regression coverage added |
| P4-069 | P0 | Include Phase 6 occurrences and preferences in privacy export | Privacy/Backend | P4-068 | **Complete for repository scope:** canonical export includes care occurrences and notification preferences while excluding device/FCM credentials; regression coverage added |
| P4-070 | P0 | Include agent-domain state in privacy export and deletion | Privacy/Backend | P4-069 | **Complete for repository scope:** agent sessions/runs, context requests, and action records are exported and owner-purged from memory and durable storage; regression coverage added |
| P4-071 | P0 | Include agent-domain rows in deletion residual verification | Privacy/Security | P4-070 | **Complete for repository scope:** agent sessions, runs, context requests, and actions are now independently counted after deletion; attachment wiring is covered and manifest hashes rebuilt |
| P4-072 | P0 | Delete exported support cases and verify operations residuals | Privacy/Backend | P4-071 | **Complete for repository scope:** support cases are attached to privacy residual verification and removed during account deletion; regression coverage added |
| P4-073 | P0 | Redact credential digests from privacy exports | Privacy/Security | P4-072 | **Complete for repository scope:** future invitation/share payloads and portability share grants no longer export token-verification digests; regression coverage added |
| P4-074 | P1 | Expand release traceability from phase-only to domain-level controls | Release/QA | P4-073 | **Complete for repository scope:** matrix expanded to 27 requirement rows with implementation, local-evidence, and external-gate columns; checker passes |
| P4-075 | P1 | Re-run local specialist Phase 8–11 acceptance harness | Specialist/QA | P4-074 | **Complete for repository scope:** Floci harness passed 17 regression tests and 2/2 local fixture cases; real provider/device certification remains external |
| P4-076 | P0 | Register operations residual inventory at privacy-service construction | Privacy/Security | P4-075 | **Complete for repository scope:** directly injected operations services now receive the same support-case residual verification as runtime-attached services; regression coverage added |
| P4-077 | P1 | Preserve domain-level traceability during evidence regeneration | Release/QA | P4-076 | **Complete for repository scope:** release evidence builder emits all 27 traceability rows; checker and manifest gates pass after regeneration |
| P4-078 | P0 | Redact purchase tokens from privacy exports | Privacy/Security | P4-077 | **Complete for repository scope:** premium entitlement export now uses `PremiumService.public()` and omits Google Play purchase tokens; regression coverage added |
| P4-079 | P1 | Make traceability gate require the complete domain-level matrix | Release/QA | P4-078 | **Complete for repository scope:** checker requires at least 27 rows and all critical domain IDs, preventing regression to phase-only coverage; regeneration and full tests pass |
| P4-080 | P0 | Fail closed for specialist production feature flags | Release/Security | P4-079 | **Complete for repository scope:** production-config checker rejects any specialist entry that enables execution or public exposure; regression tests cover safe-empty and unsafe-public configurations |
| P4-081 | P0 | Fail closed when specialist certification metadata is missing | Specialist/Security | P4-080 | **Complete for repository scope:** runtime specialist release validation rejects enabled/public flags without a non-empty non-`PENDING` certificate ID; regression coverage added |
| P4-082 | P0 | Prevent uncertified PETi Check activation through production environment variables | Release/Security | P4-081 | **Complete for repository scope:** production startup rejects `peti_check_enabled=true` until an externally certified release flag is supplied; regression coverage added |
| P4-083 | P0 | Make operational specialist defaults fail closed | Operations/Security | P4-082 | **Complete for repository scope:** all specialist execution/public defaults are disabled until explicit certified configuration is loaded; regression coverage added |
| P4-084 | P0 | Reject malformed durable feature-flag types | Operations/Security | P4-083 | **Complete for repository scope:** non-boolean persisted enable/kill-switch values are ignored and safe defaults retained; regression coverage added |
| P4-085 | P1 | Persist emergency variable-cost control changes | Operations/Backend | P4-084 | **Complete for repository scope:** admin variable-cost enable/disable mutations persist through the feature-flag adapter and survive service restart; regression coverage added |
| P4-086 | P1 | Persist automatic budget emergency shutdown | Operations/Backend | P4-085 | **Complete for repository scope:** budget-exceeded variable-cost operations persist the emergency disable state and retain it after restart; regression coverage added |
| P4-087 | P1 | Enforce scoped AI kill-switch validation at the service boundary | Operations/Security | P4-086 | **Complete for repository scope:** direct service callers are restricted to approved scopes and boolean values, matching the API contract; regression coverage added |
| P4-088 | P0 | Enforce administrator authorization for scoped AI kill-switch mutations | Operations/Security | P4-087 | **Complete for repository scope:** service-level mutation requires `ADMIN` and API passes the authenticated role; regression coverage added |
| P4-089 | P1 | Enforce strict boolean types on operational controls | Operations/Security | P4-088 | **Complete for repository scope:** global AI and variable-cost controls reject non-boolean direct inputs instead of coercing truthy values; regression coverage added |
| P4-090 | P1 | Reject malformed variable-cost estimates before budget evaluation | Operations/Billing | P4-089 | **Complete for repository scope:** negative, boolean, and non-integer estimated cost units are rejected rather than normalized into a budget decision; regression coverage added |
| P4-091 | P0 | Reapply persisted AI kill switches after service restart | Operations/AI/Security | P4-090 | **Complete for repository scope:** startup reapplies durable global/provider/model/species kill switches to `AnalysisService`, filtering malformed nested values; regression coverage added |
| P4-092 | P0 | Preserve static AI baseline when global kill switch is cleared | Operations/AI/Security | P4-091 | **Complete for repository scope:** clearing the runtime global switch restores only the configured AI baseline and cannot enable a statically disabled deployment; regression coverage added |
| P4-093 | P0 | Make specialist task completion idempotent under concurrent redelivery | Specialist/Billing/Security | P4-092 | **Complete for repository scope:** completion, funding consumption, candidate creation, and durable write are serialized; concurrent duplicate-delivery regression proves one funding consume |
| P4-094 | P0 | Make agent task execution idempotent under concurrent redelivery | Agents/AI/Security | P4-093 | **Complete for repository scope:** provider execution and terminal run persistence are serialized per executor; concurrent duplicate-delivery regression proves one provider call |
| P4-095 | P0 | Persist terminal failure for unexpected agent execution errors | Agents/Reliability/Security | P4-094 | **Complete for repository scope:** unexpected provider/serialization failures transition durable agent runs to `FAILED` instead of leaving them stuck in `RUNNING`; regression coverage added |
| P4-096 | P0 | Prevent internal task business failures from being misclassified as authentication failures | API/Security/Reliability | P4-095 | **Complete for repository scope:** internal maintenance, notification, specialist, and record-extraction handlers map only authentication failures to 401; downstream failures retain domain/500 handling; regression coverage added |
| P4-097 | P0 | Persist analysis kill-switch terminal failures | Analysis/Operations/Security | P4-096 | **Complete for repository scope:** global/provider/model/species kill-switch failures now persist `FAILED_FINAL` and error reason through the job repository; restart regression coverage added |
| P4-098 | P1 | Record terminal failure timestamps for analysis fail-closed paths | Analysis/Operations/QA | P4-097 | **Complete for repository scope:** economics-policy and AI kill-switch terminal failures now set `failed_at`; regression assertions cover both paths |
| P4-099 | P0 | Serialize Phase 6 notification dedupe and delivery | Notifications/Privacy/Reliability | P4-098 | **Complete for repository scope:** concurrent dispatches serialize the dedupe check, provider send, and durable delivery marker; regression proves one provider send |
| P4-100 | P0 | Serialize Phase 6 occurrence actions under duplicate delivery | Care/Automation/Reliability | P4-099 | **Complete for repository scope:** occurrence idempotency, recurring successor creation, and durable mutation are serialized; concurrent regression proves one successor |
| P4-101 | P0 | Serialize media retention expiry sweeps under duplicate delivery | Media/Privacy/Reliability | P4-100 | **Complete for repository scope:** due and abandoned-upload sweeps serialize object deletion, terminal-state persistence, and session expiry; concurrent regression proves one expiry |
| P4-102 | P0 | Serialize account deletion idempotency and destructive execution | Privacy/Security/Reliability | P4-101 | **Complete for repository scope:** deletion state-machine creation, cascade execution, residual verification, and terminal persistence are serialized; concurrent regression proves one execution and one replay |
| P4-103 | P0 | Serialize collaboration and invitation access-state mutations | Collaboration/Security/Reliability | P4-102 | **Complete for repository scope:** membership grant/revoke and invitation consumption are serialized at the service boundary to prevent concurrent access-state races and token replay windows |
| P4-104 | P1 | Serialize collaboration authorization reads with access mutations | Collaboration/Security/QA | P4-103 | **Complete for repository scope:** membership authorization reads are protected against concurrent map mutation and inconsistent access decisions |
| P4-105 | P0 | Enforce authenticated invitee matching at invitation acceptance | Future/Security/Privacy | P4-104 | **Complete for repository scope:** invitation consumption accepts an optional expected identity and the authenticated API caller must match the stored invitee; mismatch regression added |
| P4-106 | P0 | Redact portability share digests from revocation responses | Portability/Security/Privacy | P4-105 | **Complete for repository scope:** revoked-share public responses omit `token_digest`; regression coverage added |
| P4-107 | P1 | Serialize portability share and invitation access lookups | Portability/Future/Security | P4-106 | **Complete for repository scope:** share creation, revocation, resolution, and invitation token lookup are protected against concurrent mutable-map races |
| P4-108 | P1 | Keep credential-bearing access maps synchronized during lookup and mutation | Portability/Future/Security | P4-107 | **Complete for repository scope:** portability share operations and future invitation lookup use re-entrant service locks, preserving linearizable local access decisions |
| P4-109 | P1 | Normalize malformed portability-share API TTL input into a client error | Portability/API/QA | P4-108 | **Complete for repository scope:** invalid TTL conversion is caught and returned as `SHARE_POLICY_INVALID` HTTP 400; API regression added |
| P4-110 | P0 | Enforce strict boolean raw-media export controls | Portability/Privacy/API | P4-109 | **Complete for repository scope:** API and service boundaries reject non-boolean `include_raw_media` values, preventing truthy-string coercion from broadening exports; regression added |
| P4-111 | P1 | Enforce strict boolean automation enablement controls | Automation/API/Security | P4-110 | **Complete for repository scope:** automation API rejects non-boolean `enabled` values instead of truthy-coercing strings; regression added |
| P4-112 | P1 | Validate collaboration membership TTL types at the service boundary | Collaboration/API/Security | P4-111 | **Complete for repository scope:** malformed, boolean, non-positive, and non-numeric TTL values are rejected with `MEMBERSHIP_TTL_INVALID` rather than escaping as server errors |
| P4-113 | P1 | Enforce strict notification enablement types | Phase 6/Privacy/API | P4-112 | **Complete for repository scope:** care-item and notification-preference enablement reject truthy-string coercion at the service boundary; regression coverage added |
| P4-114 | P1 | Keep rejected notification preference mutations side-effect free | Phase 6/Privacy/QA | P4-113 | **Complete for repository scope:** notification preference type validation occurs before lazy default creation, so invalid requests create no preference state; regression added |
| P4-115 | P0 | Persist and durably delete operational support cases | Operations/Privacy/Reliability | P4-114 | **Complete for repository scope:** support cases hydrate from durable storage, writes persist on creation/update, and account deletion removes durable rows as well as in-memory state; restart/delete regression added |
| P4-116 | P1 | Configure deployable public privacy and account-deletion web resources | Release/Platform/Legal | P4-115 | **Complete for repository scope:** Firebase Hosting now publishes `release/prod/web`; structural regression verifies the home, privacy, and deletion pages exist; HTTPS publication and legal approval remain external |
| P4-117 | P0 | Preserve Firestore document IDs during generic durable hydration | Persistence/Privacy/Operations | P4-116 | **Complete for repository scope:** shared Firestore adapter injects canonical document IDs into `all`, owner-scoped, and user-scoped rows; support-case restart hydration regression added |
| P4-118 | P1 | Reconcile stale completion-audit test counts with current evidence | Release/QA | P4-117 | **Complete for repository scope:** completion audit now reports the current workspace baseline and labels older frozen evidence as historical rather than current release proof |
| P4-119 | P1 | Reconcile stale gap-analysis remediation lists | Release/QA | P4-118 | **Complete for repository scope:** gap-analysis entries now distinguish implemented local tests from genuinely pending live provider, cloud, device, Play, and legal evidence |
| P4-120 | P1 | Fail closed on incomplete specialist evaluation manifests | Specialist/Release/QA | P4-119 | **Complete for repository scope:** all 16 specialist split manifests now undergo schema, metadata, required-contract, and field-type validation in local CI; provider execution and certificates remain external |
| P4-121 | P1 | Preserve Firestore IDs in media adapter hydration | Media/Persistence/Privacy | P4-120 | **Complete for repository scope:** media metadata and repository adapters restore canonical document IDs for legacy rows; regression coverage added |
| P4-122 | P1 | Serialize Future-domain API mutations at the service boundary | Future/Automation/Reliability | P4-121 | **Complete for repository scope:** saved-search, collection, automation-rule, and suggestion transitions now use locked service mutations with strict enablement validation; API concurrency regression coverage added |
| P4-123 | P1 | Serialize Future-domain creation and owner-scoped reads | Future/Automation/Reliability | P4-122 | **Complete for repository scope:** Future item creation, ownership lookup, and listing now share the service lock with mutations and deletion, preventing local mutable-map races |
| P4-124 | P1 | Remove Future API access to private mutation/validation internals | Future/API/Security | P4-123 | **Complete for repository scope:** import confirmation uses locked transition, and pet existence checks use the public locked assertion boundary; no Future private helper calls remain in API routes |
| P4-125 | P1 | Serialize Future search and assistant-thread mutations | Future/Assistant/Reliability | P4-124 | **Complete for repository scope:** owner-scoped search and assistant message append/persistence now execute under the Future service lock, preventing concurrent mutable-state races |
| P4-126 | P0 | Route privacy Future export/deletion through synchronized service APIs | Future/Privacy/Security | P4-125 | **Complete for repository scope:** privacy export uses locked owner snapshots and account deletion uses locked durable owner deletion; direct `future.items` iteration is removed from privacy orchestration |
| P4-127 | P1 | Make Future durable hydration resilient to transient store outages | Future/Persistence/Reliability | P4-126 | **Complete for repository scope:** Future startup catches durable `all()` read failures and starts with an empty projection rather than crashing; regression coverage added |
| P4-128 | P1 | Make media and credit hydration resilient to transient store outages | Media/Credits/Persistence | P4-127 | **Complete for repository scope:** media metadata and credit journal reads fail safely during startup outages; regression coverage added |
| P4-129 | P1 | Make agent, specialist, and report hydration resilient to store outages | Agents/Specialists/Reports/Persistence | P4-128 | **Complete for repository scope:** startup reads for agent, specialist, and weekly-report projections fail safely per collection; regression coverage added |
| P4-130 | P1 | Serialize automation rule evaluation and persistence | Automation/Reliability | P4-129 | **Complete for repository scope:** rule creation and evaluation now hold a service lock across deduplication, state mutation, and durable persistence; concurrent duplicate-delivery regression added |
| P4-131 | P1 | Skip malformed agent auxiliary rows during hydration | Agents/Persistence/Reliability | P4-130 | **Complete for repository scope:** malformed context-request and action rows are rejected inside the per-row boundary without preventing startup; regression coverage added |
| P4-132 | P0 | Make Phase 6 hydration resilient per collection | Care/Notifications/Persistence | P4-131 | **Complete for repository scope:** measurements, care, occurrences, preferences, devices, deliveries, and idempotency reads fail safely per unavailable or malformed collection; regression coverage added |
| P4-133 | P1 | Make records and premium hydration resilient to store outages | Records/Billing/Persistence | P4-132 | **Complete for repository scope:** records, extraction-request, and premium-entitlement reads fail closed per unavailable durable collection; regression coverage added |
| P4-134 | P1 | Make reward-intent hydration resilient to store outages | Advertising/Credits/Persistence | P4-133 | **Complete for repository scope:** reward intents and provider-transaction dedupe rows fail closed independently when durable reads are unavailable; regression coverage added |
| P4-135 | P1 | Skip non-mapping Phase 6 durable rows during hydration | Care/Notifications/Persistence | P4-134 | **Complete for repository scope:** Phase 6 row conversion is inside the per-record validation boundary, so malformed raw rows are skipped without startup failure; regression coverage added |
| P4-136 | P1 | Serialize advanced care-record mutations and reads | Care/Privacy/Reliability | P4-135 | **Complete for repository scope:** advanced care create, update, delete, and list operations now share a re-entrant service lock across ownership checks, state mutation, and durable persistence |
| P4-137 | P1 | Serialize personal-memory mutations, invalidation, and reads | Memory/Assistant/Privacy/Reliability | P4-136 | **Complete for repository scope:** memory refresh, listing, source invalidation, and owner deletion now share a re-entrant lock across in-memory and durable state |
| P4-138 | P1 | Serialize reward-intent owner reads | Advertising/Credits/Reliability | P4-137 | **Complete for repository scope:** reward-intent lookup now shares the service lock with creation and callback verification, preventing mutable-map races |
| P4-139 | P1 | Serialize premium entitlement owner reads | Billing/Security/Reliability | P4-138 | **Complete for repository scope:** current-entitlement selection and expiry projection now share the reconciliation lock, preventing partially observed billing state |
| P4-140 | P1 | Reconcile stale Phase 17 public-web checklist language | Release/Legal/QA | P4-139 | **Complete for repository scope:** pending checklist now distinguishes existing hosted source pages and Firebase configuration from still-pending public HTTPS reachability and legal approval |
| P4-141 | P1 | Reject coercive portability-share TTL input | Portability/API/Security/QA | P4-140 | **Complete for repository scope:** share creation accepts only JSON integer TTL values and rejects booleans, fractional numbers, and numeric strings with a client error; boundary regression added |
| P4-142 | P1 | Reconcile current backend test baseline after portability hardening | Release/QA | P4-141 | **Complete for repository scope:** qualification plan and gap analysis now report the authoritative baseline while preserving historical evidence counts |
| P4-143 | P1 | Prevent coercive search-limit normalization | Search/API/Security/QA | P4-142 | **Complete for repository scope:** boolean and fractional search limits now use the safe default rather than being silently converted; numeric-string compatibility and regression coverage are retained |
| P4-144 | P1 | Close provisioning and admin-ownership documentation/test gaps | Auth/Release/QA | P4-143 | **Complete for repository scope:** provisioning's Firestore constructor and ADMIN/INTERNAL_TEST ownership isolation now have explicit regression coverage; live Firestore contention remains external |
| P4-145 | P1 | Reconcile Phase 1 capability-pack documentation | Species/Release/QA | P4-144 | **Complete for repository scope:** Phase 1 exit audit now reflects the versioned DOG/CAT registry while preserving the historical empty-capability design rule and external release-certification boundary |
| P4-146 | P1 | Reconcile stale specialist harness checklist language | Specialist/Release/QA | P4-145 | **Complete for repository scope:** Phase 0–10 checklist now references the existing Phase 8–11 Floci harness; executing it against the required emulator/provider environment remains an evidence gate |
| P4-147 | P1 | Reconcile stale extended-domain test-coverage audit | Release/QA | P4-146 | **Complete for repository scope:** gap analysis now records the existing extended-domain local suites while retaining the out-of-canonical-scope and external-certification warnings |
| P4-148 | P1 | Make search projections resilient to malformed source rows | Search/Persistence/Reliability | P4-147 | **Complete for repository scope:** search skips non-mapping source rows instead of failing the query; regression coverage added |
| P4-149 | P1 | Make search projections fail closed on source outages | Search/Persistence/Reliability | P4-148 | **Complete for repository scope:** search returns an empty result when its non-authoritative source provider is unavailable; outage regression added |
| P4-150 | P0 | Enforce pet scoping for portability exports | Privacy/Portability/Security | P4-149 | **Complete for repository scope:** production portability wiring now uses a pet-scoped privacy projection and excludes sibling-pet/account-wide rows; regression coverage added |
| P4-151 | P1 | Map portability export ownership failures to the API contract | Portability/API/Security/QA | P4-150 | **Complete for repository scope:** missing or non-owned pet exports return the standard 404 anti-enumeration response instead of an unhandled server error; regression added |
| P4-152 | P1 | Enforce memory-route pet ownership boundary | Memory/API/Privacy/Security | P4-151 | **Complete for repository scope:** memory reads now reject missing or non-owned pets with the standard 404 response instead of returning an ambiguous empty projection; regression added |
| P4-153 | P1 | Enforce pet ownership before portability-share creation | Portability/API/Privacy/Security | P4-152 | **Complete for repository scope:** share creation rejects missing or non-owned pets before issuing a share grant; regression added |
| P4-154 | P1 | Reject coercive caregiver-invitation TTL input | Future/Collaboration/API/Security | P4-153 | **Complete for repository scope:** invitation creation rejects booleans, fractional values, and numeric strings instead of allowing comparison/type errors or silent coercion; regression added |
| P4-155 | P1 | Enforce portability TTL types at the domain boundary | Portability/Security/Reliability | P4-154 | **Complete for repository scope:** direct portability service callers now receive `SHARE_POLICY_INVALID` for boolean, fractional, or string TTL values; regression coverage added |
| P4-156 | P1 | Fail closed on malformed portability import flags | Portability/Privacy/Security | P4-155 | **Complete for repository scope:** import integrity verification rejects non-boolean raw-media manifest values and malformed packages without coercion; regression coverage added |
| P4-157 | P1 | Validate portable-import package shape before integrity hashing | Portability/Privacy/Security | P4-156 | **Complete for repository scope:** import preview rejects non-string pet identifiers and non-object sections before digest verification; regression coverage added |
| P4-158 | P1 | Reject coercive premium acknowledgement fields | Billing/Security/QA | P4-157 | **Complete for repository scope:** verified entitlement responses must contain boolean acknowledgement fields; malformed truthy values fail closed before persistence; regression coverage added |
| P4-159 | P1 | Fail closed on malformed portability share credentials | Portability/Security/API | P4-158 | **Complete for repository scope:** share resolution rejects non-string IDs/tokens with the generic not-found contract instead of propagating attribute errors; regression coverage added |
| P4-160 | P1 | Fail closed on malformed invitation credentials | Future/Collaboration/Security | P4-159 | **Complete for repository scope:** invitation token lookup treats non-string credentials as absent and returns the documented not-found/expired error without hashing attribute failures; regression added |
| P4-161 | P1 | Make Firestore analysis reads resilient to malformed durable rows | Analysis/Persistence/Reliability | P4-160 | **Complete for repository scope:** analysis job reads centralize safe hydration and skip invalid status/schema rows instead of crashing; regression coverage added |
| P4-162 | P1 | Make Firestore analysis-result reads resilient to malformed rows | Analysis/Persistence/Reliability | P4-161 | **Complete for repository scope:** result lookup now validates durable row shape and returns no result for malformed documents; regression coverage added |
| P4-163 | P1 | Make Firestore credit reservation allocation resilient to malformed grant amounts | Credits/Persistence/Reliability | P4-162 | **Complete for repository scope:** transactional allocation skips grants whose remaining or reserved amounts are non-numeric or boolean, preventing malformed durable rows from corrupting reservation arithmetic; regression coverage added |
| P4-164 | P1 | Make Firestore credit transitions fail closed on malformed grant amounts | Credits/Persistence/Reliability | P4-163 | **Complete for repository scope:** consume/release transitions reject malformed remaining, reserved, or allocation amounts with the existing ledger-invariant error before any durable write; regression coverage added |
| P4-165 | P1 | Enforce non-negative Firestore credit balance invariants | Credits/Persistence/Reliability | P4-164 | **Complete for repository scope:** reservation eligibility rejects negative durable balances and transitions reject negative balances or non-positive allocations before writing; regression coverage added |
| P4-166 | P1 | Validate Firestore credit reservation request amounts | Credits/Persistence/Reliability | P4-165 | **Complete for repository scope:** direct adapter callers cannot submit boolean, fractional, string, zero, or negative reservation amounts; regression coverage added |
| P4-167 | P1 | Prevent Firestore credit transition balance underflow | Credits/Persistence/Reliability | P4-166 | **Complete for repository scope:** consume/release transitions reject allocations exceeding reserved or remaining balances before durable writes; regression coverage added |
| P4-168 | P1 | Reject unknown Firestore credit transition modes | Credits/Security/Reliability | P4-167 | **Complete for repository scope:** the durable transition adapter accepts only canonical consume/release modes and rejects malformed direct callers; regression coverage added |
| P4-169 | P1 | Validate Firestore credit allocation shapes before transitions | Credits/Persistence/Reliability | P4-168 | **Complete for repository scope:** malformed reservation allocation lists and entries now fail with the ledger-invariant error instead of propagating key/type errors; regression coverage added |
| P4-170 | P1 | Enforce integer credit quantities in Firestore journals | Credits/Persistence/Reliability | P4-169 | **Complete for repository scope:** durable grant balances and transition allocations reject fractional values, matching the integer credit domain and preventing sub-credit ledger arithmetic; regression coverage added |
| P4-171 | P0 | Reject coercive analysis kill-switch values | Analysis/Operations/Security | P4-170 | **Complete for repository scope:** direct runtime kill-switch callers must provide actual booleans; truthy strings can no longer silently enable a safety control; regression coverage added |
| P4-172 | P0 | Reject malformed provider acceptance values | Analysis/AI/Security | P4-171 | **Complete for repository scope:** provider responses must carry an actual boolean acceptance field; truthy non-boolean values now fail closed before credit consumption or result persistence; regression coverage added |
| P4-173 | P1 | Reject coercive provider usage values | Analysis/AI/Operations | P4-172 | **Complete for repository scope:** provider token usage must be non-negative integers before cost accounting; booleans, fractions, strings, and negative values fail closed; regression coverage added |
| P4-174 | P1 | Reject coercive economics simulation inputs | Economics/Operations/Security | P4-173 | **Complete for repository scope:** scenario cost estimates now require non-negative integer inputs and reject malformed scenarios rather than silently truncating or coercing values; regression coverage added |
| P4-175 | P1 | Reject coercive Google Play purchase identifiers | Billing/Security | P4-174 | **Complete for repository scope:** Play package, product, token, and RTDN fields must be non-empty strings; malformed values fail before network lookup or entitlement processing; regression coverage added |
| P4-176 | P1 | Reject coercive premium-service purchase identifiers | Billing/Security | P4-175 | **Complete for repository scope:** PremiumService no longer stringifies malformed product or purchase-token fields before validation; regression coverage added |
| P4-177 | P1 | Reject malformed premium event identifiers | Billing/Security/Reliability | P4-176 | **Complete for repository scope:** premium reconciliation rejects non-string or blank event IDs before set membership and entitlement mutation; regression coverage added |
| P4-178 | P1 | Reject malformed verified subscription identifiers | Billing/Security | P4-177 | **Complete for repository scope:** verified subscription construction rejects non-string or blank package, product, and purchase-token fields instead of stringifying them; regression coverage added |
| P4-179 | P1 | Reject non-mapping Google Play RTDN payloads | Billing/Security/Reliability | P4-178 | **Complete for repository scope:** RTDN parsing rejects non-mapping payloads with the documented validation error instead of propagating attribute failures; regression coverage added |
| P5-001 | P0 | Complete deletion, privacy residual and legal review | Privacy/Legal | P2-003 | Privacy release decision |
| P6-001 | P0 | Complete physical-device/accessibility matrix | Android/QA | P1-002 | Device certificate |
| P7-001 | P1 | Execute Play billing lifecycle or formally exclude billing | Billing/Release | P1-002 | Billing certificate/scope decision |
| P8-001 | P0 | Execute operational outage, cost and recovery drills | SRE | P2-001 | SLO/drill evidence |
| P9-001 | P0 | Build/sign/inspect production AAB and complete Play gates | Release | P5/P6/P8 | Signed artifact + Play evidence |
| P9-002 | P0 | Independent review, clear blockers and sign go/no-go | Release owner | All prior | Empty blockers + signed decision |
