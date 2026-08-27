# PETi Phases 0–10 — Pending Work Checklist

**Purpose:** what is actually still open before Phases 0–10 can be called 100% complete, based on:
- the reference implementation-only checklist (`PETi_Phases_0_to_10_Implementation_Only_100pct_Checklist.md`),
- this repo's own status docs (`docs/PHASE_0_11_IMPLEMENTATION_AUDIT.md`, `docs/ALL_PHASES_IMPLEMENTATION_STATUS.md`, `docs/PHASE_6/7/8_11/9/10_IMPLEMENTATION_STATUS.md`),
- and direct inspection of the current codebase (`backend/app`, `android/`, `contracts/`, `eval/`, `infra/`).

## Bottom line

Code-level implementation for Phases 0–10 is essentially in place: every domain module, contract, ADR, API route, guardrail, and Android surface named in the build plans exists in the tree. The current backend suite has 255 passing tests; Ruff, mypy, architecture/secret checks, Android build/lint/unit checks, and the root gate are green using **local fakes** (FakeAI, FakeAuth, Floci/emulated Firestore-Storage, fake FCM). A non-production GCP sandbox topology is also applied and has an authenticated Scheduler→private-Cloud-Run maintenance smoke returning HTTP 200.

What is **not** done — and is what stands between "code exists" and "phase is complete" — falls into three buckets, all confirmed by the repo's own status docs:

1. **Full real GCP/Firebase product environment is not yet certified.** The non-production sandbox topology is applied, but full Firebase-authenticated product slices, real provider execution, and cloud-backed residual/race evidence remain pending.
2. **Full real-provider or real-device evidence remains pending.** A sandbox Scheduler→private-Cloud-Run maintenance smoke has executed successfully, but the broader real Firebase, Gemini, Cloud Tasks product, FCM, and physical-device matrix remains external.
3. **Specialist AI features have no evaluation runs or release certificates.** Initial Scan, Dental Check, and Feces Check (Phases 8–10) have eval *manifests* (`dev/held_out/red_team/regression.json`) but zero executed runs and zero release-decision artifacts. Even PETi Check (Phase 5), which does have a release-decision file, has **only FakeAI runs** behind it (every `eval/peti_check/run_*.json` is suffixed `_fake`) — no real Gemini held-out/red-team evidence exists yet.

Everything below is organized so each item is a concrete, checkable action.

---

## 1. Stand up the real cloud environment (blocks every phase's exit gate)

Terraform exists (`infra/terraform/modules/peti-platform`, per-environment roots for sandbox/staging/production) but nothing indicates it has been `apply`-ed to a live GCP project.

- [x] **INFRA-001** A dedicated non-production sandbox GCP project exists with the required core APIs enabled; real Gemini/Play/device readiness remains external.
- [x] **INFRA-002** Terraform was applied to the sandbox topology and state/outputs are recorded in `release/EXTERNAL_GATES.md`; full product certification remains pending.
- [x] **INFRA-003, INFRA-005–009, INFRA-011, INFRA-014** Sandbox service accounts/IAM, Firestore/indexes, private GCS, Cloud Run runtime settings, Cloud Tasks policy, monitoring, and environment separation are applied and captured in `release/EXTERNAL_GATES.md`; production remains separate.
- [x] **INFRA-004** Authenticated Scheduler→private Cloud Run maintenance smoke returned HTTP 200; unauthenticated access returned 403. Provider-side worker-task delivery remains a separate external slice.
- [x] **INFRA-010** Sandbox server-side AI configuration and kill-switch contract are deployed; real Gemini/Vertex quota and provider execution remain external.
- [x] **INFRA-012** Sandbox API/build configuration is documented; physical Firebase sign-in/device execution remains external.
- [ ] **INFRA-013** Run sandbox seed/reset tooling against the real project; this remains an operator execution gate.
- [ ] **INFRA-015** Prove production-project IAM denial with an independent operator identity; this requires external IAM/account evidence.

## 2. Real-provider / real-device verification evidence per phase

Every phase's build plan ends with a "Final Verification" / "Exit Gate" that requires this evidence. None of it has been produced yet — only Floci/FakeAI/emulator runs.

- [ ] **Phase 1** — Real Android → Credential Manager → real Google account → Firebase Auth → sandbox API → Firestore vertical slice; reinstall + re-auth persistence test; cross-user authorization check against real Firestore.
- [ ] **Phase 2** — Real DEV rewarded-ad smoke test using Google's official test ad unit + real SSV callback verification end-to-end (not the fake reward verifier).
- [ ] **Phase 3** — Real DEV Cloud Storage vertical slice: small (simple signed PUT) and large (resumable) upload → finalize → authorized read → delete, both against the real sandbox bucket.
- [~] **Phase 4** — Bounded real Cloud Tasks → private Cloud Run worker OIDC health smoke now passes (anonymous external access remains blocked); real Gemini image-modality output, additional modality, funding consume-once, and duplicate-delivery verification remain pending.
- [ ] **Phase 5** — Real DEV PETi Check vertical slice (real Gemini, not FakeAI); real Gemini **held-out** and **red-team** evaluation runs (`eval/peti_check` currently only has `_fake` runs); refresh `PETI_CHECK_RELEASE_DECISION_1.0.0` from real-provider evidence before treating the flag as release-eligible.
- [ ] **Phase 6** — Real Firebase/Firestore backend-restart and account-switch verification; real FCM delivery, permission-denied behavior, notification tap, and wrong-account deep-link test; physical-device process-death/reinstall, locale, DST/timezone, and accessibility review (currently only emulator/manual API-35 AVD evidence exists).
- [ ] **Phase 7** — Real DEV vertical slice: private PDF upload → secure viewer → real Gemini document extraction → Confirm/Correct/Reject → documented-fact/Timeline projection → dependency-aware deletion.
- [ ] **Phase 8 (Initial Scan)** — Execute the existing `eval/specialists/dog_initial_scan` dev/held-out/red-team manifests against real Gemini; produce evaluation-run artifacts; produce and sign an Initial Scan release certificate; run a real DEV vertical slice (real guided capture → real Gemini → candidate review → profile update).
- [ ] **Phase 9 (Dental Check)** — Same: execute `eval/specialists/dog_dental_check` manifests against real Gemini, produce run artifacts + release certificate, run a real DEV vertical slice including the safety-escalation and hidden-disease red-team cases.
- [ ] **Phase 10 (Feces Check)** — Same: execute `eval/specialists/dog_feces_check` manifests against real Gemini, produce run artifacts + release certificate, run a real DEV vertical slice covering freshness/producer-attribution rejection, black/tarry and major-blood safety escalation, and (if `feces_longitudinal_compare_enabled`) a real comparable + non-comparable longitudinal pair.

> Note: `eval/DOG_DENTAL/`, `eval/DOG_FECES/`, `eval/dog_body/`, `eval/dog_initial_scan/` currently contain only a `README.md` each — the actual manifests live under `eval/specialists/<name>/`. Consolidate or cross-link these before running evaluations so the real dataset location is unambiguous.

## 3. Specialist release governance (Phases 5, 8, 9, 10)

- [ ] Produce `DOG_INITIAL_SCAN_RELEASE_CERTIFICATE` (or equivalent) recording enabled/disabled candidate fields, evaluation run IDs, critical-violation counts, provider/model/prompt/schema/guardrail versions, go/no-go — none exists today.
- [ ] Produce `DENTAL_CHECK_RELEASE_CERTIFICATE_<version>` — none exists today.
- [ ] Produce `FECES_CHECK_RELEASE_CERTIFICATE_<version>` — none exists today.
- [ ] Re-validate/refresh `PETI_CHECK_RELEASE_DECISION_1.0.0` once real (non-fake) Gemini held-out and red-team runs exist.
- [ ] Confirm each specialist's public feature flag (`peti_check_enabled`, `dog_initial_scan_enabled`, `dog_dental_check_public_enabled`, `feces_check_public_enabled`, etc.) is left **off** for real customers until its certificate is signed.

## 4. Housekeeping / re-verification

- [x] Re-ran `scripts/check.ps1` end-to-end after the Phase 8–11 specialist work; current backend suite is 255 passed. Real provider/device certification remains a separate external gate.
- [ ] Re-run the Floci acceptance harnesses for every phase (`scripts/test-floci-phase3.ps1`, `-phase45.ps1`, `-phase7.ps1`, `phase6-floci-smoke.ps1`, and `scripts/test-floci-phase8-11.ps1`) after any infra/dependency change. The Phase 8–11 harness now exists; execution remains an evidence gate.
- [x] WEBP image support is explicitly disabled: the backend accepts only JPEG/PNG for images, while viewer/extraction validation is absent. A regression test rejects `image/webp` so the optional path cannot remain half-wired.
- [x] Confirm the Phase-3 audio capture foundation: `AudioCaptureController` uses the device microphone with explicit start/stop/cancel lifecycle, and `AudioCaptureDialog` exposes it from PETi Check; the resulting `AUDIO` `MediaSource` enters the durable upload coordinator. Physical-device microphone permission and recording QA remain external evidence gates.
- [x] Sweep `docs/adr/` for duplicate-numbered ADRs. `docs/adr/ADR_INDEX.md` now explicitly records the legacy collision set, preserves historical paths, and defines filename-plus-title as the canonical identity; new ADRs use the next unused numeric ID. This avoids silently breaking existing evidence references while keeping the index unambiguous.

---

## What is *not* in this list (already done per code + status docs)

Domain models, contracts, repositories, services, API routes, Android features, guardrails, deterministic safety policies, capability packs, error codes, and ADR content for Phases 0–10 are all present in the tree and covered by the local backend/Android test suites. The ~400-item implementation-only checklist you already have (`PETi_Phases_0_to_10_Implementation_Only_100pct_Checklist.md`) is the right reference for line-by-line naming — nothing in this document duplicates it; this document is the **delta** between "the code exists and passes locally" and "the phase is actually done."
