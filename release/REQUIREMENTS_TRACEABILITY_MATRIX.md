# Requirements Traceability Matrix

This matrix records source-level and local executable evidence. External gates remain pending until their execution artifacts are attached.

| ID | Phase | Requirement | Repository evidence | Local evidence | External gate |
|---|---:|---|---|---|---|
| INFRA-LOCAL | 0 | Environment contracts and fail-closed local mode | infra/terraform/modules/peti-platform; backend/app/config | Terraform fmt/validate; backend suite | Production GCP/IAM/indexes/Secret Manager remain pending; sandbox topology evidence attached |
| AUTH-OWNERSHIP | 1 | Authenticated owner isolation | backend/app/auth; owner-scoped services/routes | API and cross-owner tests | Firebase Auth/Firestore deployment pending |
| CRED-ATOMIC | 2 | Reservation atomicity and no negative balance | backend/app/credits | test_phase2_credits.py concurrency race | Firestore contention run pending |
| REWARD-SSV | 2 | Replay-safe rewarded credit grant | backend/app/advertising | test_google_ssv.py; test_phase2_rewards.py | AdMob SSV delivery pending |
| MEDIA-STATE | 3 | Authoritative media finalize and legal transitions | backend/app/media | media, retention and checksum tests | Private GCS/IAM/log review pending |
| MEDIA-ANDROID | 3 | Picker, CameraX, audio capture and resilient upload | android/app/src/main/.../media | Gradle unit/lint/build gates | Physical device matrix pending |
| AI-WORKER-AUTH | 4 | Customer tokens rejected by private worker | backend/app/main_worker.py; task auth | worker surface/bearer tests; bounded Cloud Tasks OIDC health smoke | Generic agent and specialist OIDC worker slices evidenced; full analysis-task duplicate-delivery matrix pending |
| AI-IDEMPOTENCY | 4 | Duplicate task delivery claims one job | analysis repositories and claim path | claim concurrency and Firestore adapter tests | Real Firestore transaction pending |
| AI-SAFETY | 4–5 | Provider-independent safety and guardrails | backend/app/safety; analysis/service.py; eval/peti_check/run_gemini.py | safety precedence and real Gemini PETi Check held-out/red-team suites | Evaluated sandbox configuration passed; exact frozen-RC and specialist certification remain pending |
| FLAGS | 4/15 | Global and scoped kill switches fail closed | operations/platform.py; operations/controls.py | AI kill-switch and controls tests | Multi-instance propagation drill pending |
| RECORDS-REVIEW | 7 | Candidate facts require terminal human review | backend/app/records/vault.py | records tests and API flow | Real OCR/provider execution pending |
| SPECIALISTS | 8–11 | Species/capability guards and profile writeback | backend/app/specialists | specialist and forbidden-language suites | Gemini/device certification pending |
| REPORTS | 12 | Deterministic weekly report and safe narration | eval/weekly_report; report service/validator | local four-split evaluation | Narration/scheduler/delivery pending |
| BILLING | 13 | Entitlement mapping and reconciliation | backend/app/billing; Android funding | billing security/concurrency tests | Play product/RTDN lifecycle pending |
| PRIVACY | 14 | Deletion, tombstone, task freeze and residual checks | backend/app/privacy | privacy dependency/residual/identity tests | Live Firestore/GCS race pending |
| PRIVACY-PHASE6 | 14 | Export and erase measurements, care graph, notification preferences and idempotency state | backend/app/privacy/service.py; backend/app/phase6.py | Phase 6 lifecycle and privacy export/deletion tests | Real Firestore residual-zero and reinstall evidence pending |
| PRIVACY-AGENTS | 14 | Export and erase agent sessions, runs, context requests and actions | backend/app/agents/contracts.py; backend/app/privacy/service.py | Agent/privacy domain regression tests | Live queued-worker deletion race pending |
| PRIVACY-OPS | 14–15 | Erase support cases and verify no owner-scoped residual remains | backend/app/operations/platform.py; backend/app/privacy/service.py | Privacy residual/support-case tests | Production retention/legal decision pending |
| PRIVACY-CREDENTIALS | 14/21 | Portable exports never disclose token-verification material | backend/app/future/service.py; backend/app/portability/service.py | Privacy export and token-security tests | Independent privacy/security review pending |
| PORTABILITY-INTEGRITY | 21 | Portable package provenance and tamper detection | backend/app/portability/service.py | portability integrity/access tests | Real interoperability partner/device evidence pending |
| CARE-COLLAB-AUTOMATION | 20/22/23 | Durable care, collaboration and automation state survives restart and remains owner-scoped | backend/app/care_advanced; backend/app/collaboration; backend/app/automation | persistence and authorization suites | Deployed multi-instance contention pending |
| ASSISTANT-MEMORY | 24/25 | Personal memory and grounded answers remain pet-scoped and source-bounded | backend/app/search/memory.py; backend/app/assistant/grounding.py | memory and assistant grounding tests | Real provider held-out certification pending |
| BILLING-TOKEN-BOUNDARY | 2/13 | Reward/purchase verification binds provider, owner and replay state | backend/app/advertising; backend/app/billing | reward and premium security suites | Real AdMob/Play lifecycle pending |
| RELEASE-EVIDENCE-INTEGRITY | 16 | Evidence artifact existence and hashes fail closed | scripts/build_release_evidence.py; scripts/check_release_manifests.py | release-manifest integrity tests and gate | Signed RC and independent approval pending |
| OPERATIONS | 15 | Metrics, redacted logs, cost gate and reconciliation | infra/terraform; backend/app/operations | metric/logging/reconciliation gates | Staging drills and telemetry pending |
| RELEASE-STATIC | 16 | Release manifests, artifact inspection and static gates | release/*; scripts/release_gate_check.py | static release gates | Signed AAB/security/device evidence pending |
| RELEASE-PRODUCTION | 17 | Production config, rollback and submission | release rollback/go-no-go; web source | source manifest and fail-closed checks | Production GCP/HTTPS/Play pending |
