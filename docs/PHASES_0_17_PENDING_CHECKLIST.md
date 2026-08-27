# PETi Phases 0–17 — Pending Work Checklist

**Supersedes:** `docs/PHASES_0_10_PENDING_CHECKLIST.md` (kept for history; this doc extends the same methodology through Phase 17).

**Method:** cross-referenced the 18 build plans (Phase 0–17) against this repo's own status/audit docs (`docs/PHASE_*_IMPLEMENTATION_STATUS.md`, `docs/PHASE_0_11_IMPLEMENTATION_AUDIT.md`, `docs/PHASE_12_25_IMPLEMENTATION_AUDIT.md`, `docs/RELEASE_READINESS.md`) and direct inspection of `backend/app/*`, `eval/*`, `infra/*`, `release/*`, `ops/*`.

## Bottom line

The pattern from Phases 0–10 continues, but gets **worse** the further into the plan you go:

- **Phases 0–10:** code-level implementation is essentially complete and passes locally. Cloud-backed evidence now covers the bounded Gemini PETi Check evaluation, generic agent path, and specialist worker persistence; customer-auth/upload and complete product-domain evidence remain open.
- **Phase 11 (Body Check):** code + eval fixture manifests exist and a real red-team smoke has executed with schema/guardrail checks; full held-out/regression certification, longitudinal/device slices, and the release certificate remain open.
- **Phase 12 (Weekly Report):** deterministic manifests, local evaluation harness, grouped source sections, and safety validation are implemented. Real Gemini narration, scheduler, delivery, and device evidence remain pending.
- **Phase 13 (Premium/Billing):** the backend state machine, purchase normalization, idempotent allowance grants, RTDN payload normalization, and shared reconciliation boundary are implemented. Real Google Play product, RTDN delivery, and license-tester evidence remain pending.
- **Phase 14 (Privacy/Deletion):** dependency resolution, account-deletion job state, idempotency, export assembly, and residual-verification primitives are implemented. No real GCS/Firestore residual or race evidence has run.
- **Phase 15 (Observability/Economics):** monitoring-as-code, SLOs, cost attribution, budget controls, shared reconciliation primitives, and runbooks are implemented. No production operational drills have run.
- **Phase 16 (Full Testing & Certification):** this phase's deliverable is *executed evidence*. Static gates, sandbox topology, bounded provider/agent/specialist slices, and an internal Android artifact are now evidenced; cross-user authorization, residual-data, full certification, accessibility/device, billing, and production-release gates remain open.
- **Phase 17 (Release Engineering/Play Submission):** same situation — `release/FINAL_GO_NO_GO.md` explicitly states *"This implementation pass does not assert those external gates as passed."* No signed production AAB, no Play Console account interaction, no production Firebase project exist.

In short: **repository-side implementation is substantially complete through the local portions of Phases 0–17. Remaining work is chiefly real-environment execution, certification, compliance, and production release, requiring live GCP, Gemini, Google Play, physical devices, and production credentials.** The operator sequence and evidence requirements are documented in [`docs/runbooks/EXTERNAL_QUALIFICATION_EXECUTION_CHECKLIST.md`](runbooks/EXTERNAL_QUALIFICATION_EXECUTION_CHECKLIST.md).

## Implementation update — repository-side work completed

The following locally implementable pieces have now been added:

- Deterministic Weekly Report manifests for `dev`, `held_out`, `red_team`, and `regression` under `eval/weekly_report/`, plus `eval/weekly_report/run.py`.
- Versioned monitoring-as-code declarations in `infra/monitoring/monitoring.yaml`, including nine dashboard tiers, low-cardinality metric policy, alerts, budgets, and the variable-cost intake kill switch.
- Customer SLO targets in `docs/operations/SLOS.md`.
- Operational runbooks for cost budgets, billing, rewards, reports, notifications, privacy residuals, accessibility, security, rollback, and exports under `docs/runbooks/`.
- Google Play entitlement states, `SubscriptionPurchaseV2` normalization, and idempotent premium allowance materialization in `backend/app/billing/`.
- Idempotent account-deletion job states and explicit residual verification in `backend/app/privacy/lifecycle.py`.
- Admin-only variable-cost intake control in `backend/app/operations/platform.py`.

These changes are source-level implementation only. They do not constitute real
Gemini, Google Play, device, Firestore, GCS, Cloud Tasks, or production release
evidence; those external gates remain unchecked below.

---

## 1. Carry forward: Phases 0–10 pending items

Everything in [`docs/PHASES_0_10_PENDING_CHECKLIST.md`](PHASES_0_10_PENDING_CHECKLIST.md) still applies unchanged:

- [x] Stand up the bounded sandbox GCP/Firebase environment (INFRA-001…015: Cloud Run, service accounts, Cloud Tasks OIDC, Firestore/GCS, and Firebase Auth configuration); production and full customer-authenticated staging remain external gates.
- [x] Add a reproducible Firebase Emulator Suite configuration for local Auth/Firestore/Storage matrix execution; this supplements but does not replace the real Firebase staging gate.
- [ ] Produce complete real-provider/real-device vertical-slice evidence for Phases 1–7 (Firebase Auth, GCS upload, Firestore restart/account-switch, real FCM, and real document extraction remain pending; Cloud Tasks→worker OIDC and bounded Gemini/agent slices are evidenced).
- [x] Execute real Gemini held-out + red-team evaluation runs for Phase 5 (PETi Check) and refresh the evaluated-config release decision from real evidence. Exact frozen-RC certification remains a separate gate.
- [ ] Execute the complete real Gemini held-out + red-team/regression certification for Phases 8–10 (Initial Scan, Dental, Feces). Real specialist smoke evidence exists, but complete matrices and independent certificates remain pending.
- [x] Housekeeping implementation: legacy duplicate ADR numbers are indexed in `docs/adr/ADR_INDEX.md`, WEBP/audio-capture decisions are recorded in `docs/adr/ADR-191-media-format-and-audio-capture.md`, and the local harness is available as `scripts/test-floci-phase8-11.ps1`. Full execution remains an evidence gate.

## 2. Phase 11 — Body Check

- [ ] Execute the complete `eval/specialists/dog_body_check/{dev,held_out,red_team,regression}.json` matrix against real Gemini; a real red-team smoke artifact exists, while the remaining splits and frozen-RC binding remain pending.
- [ ] Produce an externally backed `BODY_CHECK_RELEASE_CERTIFICATE_<version>`; a source-side pending certificate exists under `release/evaluation/`.
- [ ] Run the real DEV vertical slice (standardized side/top capture → real Gemini → `BodyCheckResultV1` → comparison) and the real longitudinal slice (comparable pair + deliberately non-comparable pair).
- [x] Keep `dog_body_ai_weight_estimate_enabled` explicitly disabled; the dedicated calibration evaluation is therefore a pre-enable gate, not a current release requirement.
- [ ] Physical-device capture review (§133 of the plan): camera framing, body-in-frame guidance, prior-view reference thumbnail, rotation — none of this has been exercised on a real device.

## 3. Phase 12 — Weekly PETi Report

- [x] Populate the weekly-report evaluation dataset in `eval/weekly_report/{dev,held_out,red_team,regression}/` with the required deterministic and adversarial history types.
- [x] Implement the deterministic-core evaluation harness and safety validator; local runs pass for dev, held-out, red-team, and regression fixtures. Real Gemini narration and device evidence remain separate gates.
- [x] Run the optional real Gemini narration held-out evaluation and pass the schema/safety gates: 7/7 cases passed in `release/evidence/phase12/weekly-report-narration-real-2026-08-26.json`. Exact frozen-RC binding and scheduler/device delivery evidence remain pending.
- [ ] Produce `WEEKLY_REPORT_RELEASE_DECISION_1.0.0` from real evidence; the source-side decision and local four-split evaluation artifacts exist under `release/evaluation/`, but external narration/device evidence is still pending.
- [ ] Real DEV vertical slice: real scheduler/dispatcher (or operator-triggered) closed-week generation → deterministic sections → optional real narration → Android detail → source deep links. Never executed.
- [ ] Real delivery slice if FCM/email is enabled — one dedup'd notification/email with authenticated deep link.
- [ ] Duplicate-scheduler and week-boundary/DST test evidence (§110–111) — needs execution against the real scheduler, not just unit fixtures.

## 4. Phase 13 — Premium / Google Play Billing

`backend/app/billing/` (~134 lines) is a boundary, not the full lifecycle machinery the plan requires. Concretely still needed:

- [x] Implement the billing state machine, purchase mapping, idempotent acknowledgement/allowance grants, and shared reconciliation paths. Live Play Console/RTDN and license-tester evidence remain pending.
- [ ] Create a real Google Play Console product (Premium subscription + base plan(s)); this cannot be done from this workspace and requires a live Play Developer account.
- [x] Add Pub/Sub RTDN topic/subscription IaC and a trusted, owner-resolving, replay-safe receiver in `backend/app/billing/rtdn.py`; real Google Play delivery and end-to-end dedup evidence remain pending.
- [ ] Run the full Play license-tester lifecycle suite for real: initial purchase, pending→approved/declined, accelerated renewal, grace period, account hold, recovery, involuntary churn (plan §138–144). None of this has been executed — it requires a live Play Console + license testers.
- [x] Add local abuse-contract coverage for forged verification, wrong product, cross-account token replay, and duplicate event replay in `scripts/check_billing_security.py`; real Google Play verification and package/RTDN forgery evidence remain pending.
- [ ] Release artifact inspection: no Android Publisher credential, no fake Premium override, in the actual signed AAB (can't be verified until a real signed build exists — see Phase 16/17).
- [ ] Regression: with Premium expired, confirm pets/Timeline/Measurements/Care/Records/existing results/Weekly Reports/privacy-delete remain fully usable — needs to be run against the real entitlement state machine once built.

## 5. Phase 14 — Privacy, Deletion and Retention Lifecycle

`backend/app/privacy/` (~111 lines) is likewise a boundary. Still needed:

- [x] Implement the deletion dependency resolver, account-deletion step machine, idempotency, and residual verification primitives. Live Firestore/GCS deletion and race evidence remain pending.
- [ ] Run real DEV pet deletion and real DEV account deletion against a full-feature fixture pet/account, and verify **zero residual GCS objects and zero residual Firestore payload** (plan §109–113) — never executed against real Firestore/GCS.
- [ ] Run the deletion-race matrix for real: queued AI job after delete (worker no-ops), in-flight provider call after delete (result not persisted), scheduler race, RTDN-after-delete race (plan §96–103, §687 area "Integration" tests) — these need a live queue/worker/RTDN, not just unit fakes.
- [ ] Verify reinstall-after-deletion: same Google identity signs in again, old PETi data does not return (plan §108, §117) — requires real Firebase.
- [x] Account export enumerates available canonical domains and emits a provenance/coverage manifest. Full fixture-account execution against cloud-backed stores remains pending.

## 6. Phase 15 — Observability, Economics and Production Operations

`infra/monitoring/` contains versioned monitoring-as-code plus its README. The remaining work is execution of the production operational gates. Still needed:

- [x] Implement the 9-tier dashboard hierarchy as monitoring-as-code artifacts.
- [x] Define and version customer SLOs in `docs/operations/SLOS.md` with targets and error budgets.
- [x] Implement `AICostRecord`/`ProviderPricingPolicy` and local cost attribution per operation.
- [x] Implement spend thresholds and the emergency variable-cost kill switch; production drill evidence remains pending.
- [x] Implement shared bounded, idempotent reconciliation services for analysis, funding, reward, billing, report, deletion, and notification in `backend/app/operations/reconciliation.py`; live domain drills remain pending.
- [x] Add the required operational runbooks under `docs/runbooks/`.
- [ ] Run the operational drills for real: provider outage, queue backlog, GCS failure, billing outage, reward SSV failure, deletion residual (plan §83–88) — none executed.
- [ ] Run load/cost-stress/retry-amplification tests (plan §89–95) against a real or realistic staging environment.
- [x] Add metadata-only structured logging, allowlisted fields, runtime redaction, and `scripts/check_logging_contract.py`. Production log-stream execution remains pending.

## 7. Phase 16 — Full Testing, Security Hardening and Release-Candidate Certification

This entire phase's deliverable is **executed evidence**, and the repo is explicit that it hasn't happened: `release/RC_BLOCKERS.md` states *"External blockers include real provider verification, cloud IAM/topology, billing reconciliation, residual-data evidence, accessibility review, store declarations and execution of the required certification suites."* Concretely still needed:

- [x] Generate source-backed `release/RC_MANIFEST.json` and `release/EVIDENCE_MANIFEST.json` with hashes, versions, and explicit external-pending status. A production-signed RC remains pending.
- [x] Populate `release/REQUIREMENTS_TRACEABILITY_MATRIX.md` with requirement→repository→local-evidence→external-gate mappings. The local matrix and static checks are complete; final critical-requirement certification still depends on the external execution evidence listed in the matrix.
- [ ] Run the full backend unit + integration suite against real staging Firestore/GCS/Cloud Tasks (plan §17–21) — not just Floci.
- [ ] Run the physical-device matrix (low-resource, mainstream, recent device) for critical flows: sign-in, camera, Photo Picker, SAF PDF, microphone, notifications, weight/temperature entry, Play Billing (plan §26–29).
- [ ] Run the full cross-user authorization matrix across every owner-scoped domain listed in plan §37 — for real, not just as unit fixtures.
- [ ] Run funding/reward concurrency matrix under real concurrency (one credit/two reservations, duplicate SSV, reservation terminal race) — plan §46–58.
- [ ] Run the Play Billing lifecycle suite for real (depends on Phase 13 being real first) — plan §54–61.
- [ ] Rerun PETi Check / Initial Scan / Dental / Feces / Body specialist certification against the **exact frozen RC config** with real Gemini (plan §72–83) — this is a rerun requirement even after the Phase 5/8–11 evaluations above are done once, because RC freeze requires binding evidence to one exact config.
- [ ] Run the deletion/privacy race matrix for real (plan §96–104) — depends on Phase 14 being real first.
- [ ] Run the operational kill-switch, spend-emergency, circuit-breaker, and rollback drills for real (plan §105–109) — depends on Phase 15 being real first.
- [ ] Run performance/load tests (metadata APIs, analysis creation, media, cost stress, DB contention) — plan §110–120.
- [ ] Run the accessibility regression matrix (TalkBack, non-color state, touch targets, large text) across all primary screens — plan §123–127.
- [ ] Run dependency/secret/container vulnerability scans and a static security review (auth, deserialization, upload, signed URLs, injection, logging) — plan §132–149.
- [ ] Build the actual signed release AAB and inspect it for forbidden artifacts (Gemini key, service-account JSON, local AI model files, smartphone-temperature route, debug bypass) — plan §150–161. Cannot happen without real production signing (Phase 17 prerequisite).
- [ ] Run real staging vertical slices for the full product (auth→pet→media→funding→AI→Timeline→specialists→Reports→Premium→deletion) — plan §162–167.
- [ ] Generate a real `release/EVIDENCE_MANIFEST.json` and `release/PHASE16_CERTIFICATION_REPORT.md` backed by the above, and drive `release/RC_BLOCKERS.md` to empty.

## 8. Phase 17 — Release Engineering and Google Play Submission Readiness

Same situation: `release/FINAL_GO_NO_GO.md` states *"This implementation pass does not assert those external gates as passed."* This phase fundamentally requires business/account setup outside this workspace:

- [ ] Obtain/confirm a Google Play Developer account and create the app listing.
- [ ] Freeze the production `applicationId`, `versionName`, `versionCode`; set `targetSdk = 36` (re-verify against live Play requirements at actual submission time, per the plan's own instruction to re-check official docs).
- [ ] Generate and securely store the production upload key; configure Play App Signing; write `docs/runbooks/UPLOAD_KEY_RECOVERY.md`.
- [ ] Stand up the **production** Firebase project, Cloud Run (API + worker), Firestore, private GCS, Cloud Tasks, secrets/IAM — fully separate from sandbox/staging (plan §24–35). This is a second, harder INFRA build-out beyond the sandbox one in the Phase 0–10 checklist.
- [ ] Configure production Gemini, FCM, rewarded-ad, and Play Billing product/base-plan settings (plan §33–52).
- [ ] Publish and externally verify the public HTTPS privacy policy and account-deletion web resource (`/privacy`, `/delete-account`) — plan §55–61. Source pages now exist under `release/prod/web/` and Firebase Hosting is configured to publish them; public reachability, approved controller identity, effective date, and legal approval remain external gates.
- [ ] Complete the live Google Play Data Safety, Health Apps, Permissions, Ads, Content Rating, and Target Audience forms using the *actual* current Play Console wording (plan §61–77) — the worksheets in `release/DATA_SAFETY_WORKSHEET.md` and `release/HEALTH_APPS_DECLARATION_WORKSHEET.md` exist as files; verify whether their content is real or templated, since they can only be finalized against a live Console.
- [ ] Create a dedicated reviewer/test persona with stable, documented access (not an ADMIN bypass) and verify a person outside the dev team can reach every claimed restricted feature using only `release/PLAY_REVIEWER_INSTRUCTIONS.md` (plan §79–85, §141).
- [ ] Finalize store listing copy/assets (icon, feature graphic, phone screenshots, EN/ES localization) using only real, certified screens — `release/store-listing/{en-US,es-ES}/listing.md` exist; verify they reflect actually-shipped features and contain no disallowed health/diagnostic claims (plan §87–110).
- [ ] Upload to Internal → Closed testing tracks, inspect the Play-generated/delivered artifact, and review the Play pre-launch report (plan §112–120).
- [ ] Run production smoke tests for every domain (auth, pet, PETi Check, each enabled specialist, Records, Weekly Report, Premium, deletion, kill switch) against the real production backend (plan §123–131) — depends on the production GCP build-out above.
- [ ] Prepare the rollback package (`release/ROLLBACK_PACKAGE.md`) and staged-rollout/stop-condition plan (plan §132–140) with real content.
- [ ] Produce a real `release/PHASE17_EVIDENCE_MANIFEST.json`, `release/PRODUCTION_CONFIG_SNAPSHOT.json`, and sign off `release/FINAL_GO_NO_GO.md` only once every automatic NO-GO condition (plan §173) is cleared.
- [ ] Submit for Play review and record the outcome in `release/PLAY_SUBMISSION_RECORD.md`.

---

## What is *not* in this list (already done per code + status docs)

Domain models, contracts, repositories, services, API routes, prompts/schemas/guardrails, ADRs, and Android surfaces for Phases 0–11 are in the tree and covered by local test suites. Boundary-level backend modules for Phases 12–15 (`reports/`, `billing/`, `privacy/`, `operations/`) exist and expose the documented API surface. The gap this document tracks is real-environment evidence for Phases 0–11, deeper feature-completeness plus real-environment evidence for Phases 12–15, and near-total execution for Phases 16–17, which by design require a live Google Cloud production project and a live Google Play Developer account that don't exist in this workspace.
