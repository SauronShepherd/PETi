# Phase 4/5 cloud acceptance runbook

## Controlled cloud constraint

LOCAL acceptance remains zero-cost. DEV/STAGING cloud steps are explicit
operator actions and require a reviewed project, budget, IAM, and secret
configuration. They must not run implicitly from tests or local startup.

This runbook is the operator handoff for the acceptance gates that cannot be
executed in a credential-free local checkout. Local verification must pass
before any cloud step is attempted:

```powershell
./scripts/check.ps1
```

## 1. Configure and prove DEV readiness

Provide these values through the operator environment or a secret manager;
never commit them:

```text
PETI_PROJECT_ID
PETI_TASKS_LOCATION
PETI_ANALYSIS_QUEUE_NAME
PETI_ANALYSIS_WORKER_URL
PETI_ANALYSIS_TASK_SERVICE_ACCOUNT
PETI_ANALYSIS_TASK_AUDIENCE
PETI_MAINTENANCE_EXPECTED_SERVICE_ACCOUNT
PETI_MAINTENANCE_TASK_AUDIENCE
PETI_FIREBASE_PROJECT_ID
PETI_MEDIA_BUCKET
PETI_AUTH_MODE=FIREBASE
PETI_AI_PROVIDER=GEMINI
PETI_REAL_EVAL_COMMAND=<approved evaluator command>
```

Authenticate with ADC or an active `gcloud` account, then run:

```powershell
./infra/cloudrun/preflight.ps1
```

Under the zero-cost policy, do not run the cloud deployment or DEV vertical
slice scripts. Use the local verification command instead:

```powershell
./scripts/check.ps1
```

There is no cloud deployment evidence under this policy. Record local test
commands, test counts, FakeAI provider identity, and sanitized local
correlation IDs instead.

The complete zero-cost local acceptance harness is:

```powershell
./scripts/test-floci-phase45.ps1
```

It starts only the local Floci emulators, runs the backend and Android build
checks, validates the sanitized acceptance bundle, and executes FakeAI
evaluation. It never provisions GCP or calls Gemini.

## 2. Execute customer-path evidence

Use controlled, non-sensitive DOG fixtures and capture these independent runs:

1. funded check: free/earned credit, no ad, one reservation, one consume;
2. rewarded funding: no credit, user chooses the ad, server verifies SSV,
   then one reservation;
3. abstention: completed `INSUFFICIENT_EVIDENCE` result and recapture guidance;
4. urgent: deterministic safety escalation appears before ordinary result copy;
5. reopen/process death: existing job/result is read without a new reservation,
   provider call, or ad;
6. account isolation: user A's job/result/media is inaccessible to user B.

For each run retain the job ID, result ID, reservation/ledger evidence,
provider request ID, and sanitized analytics events. Do not retain raw media,
ID tokens, signed URLs, or raw owner context in the evidence bundle.

Validate the resulting sanitized JSON bundle before archival:

```powershell
python scripts/validate_acceptance_bundle.py artifacts/phase45/acceptance_bundle.json
```

The validator requires the six scenario names above and rejects sensitive
evidence fields.

## 3. Real-cloud evaluation is an explicit external gate

Real Gemini evaluation requires an approved external project, budget,
credentials, provider configuration, and a frozen release candidate. It must
never run implicitly from local tests. Until those gates are approved, use the
deterministic FakeAI splits instead:

```powershell
python eval/run.py --suite peti_check --split dev --provider fake
python eval/run.py --suite peti_check --split regression --provider fake
python eval/run.py --suite peti_check --split held_out --provider fake
python eval/run.py --suite peti_check_red_team --provider fake
```

The release artifact remains NO-GO under this policy because no real Gemini
artifact may be generated:

```text
dangerous_under_triage
diagnosis_language
fabricated_measurement
medication_guidance
false_reassurance
schema_pass
```

The local release-decision command may still be used to prove fail-closed
behavior, but it must remain `NO-GO`:

```powershell
python eval/peti_check/release_decision.py --artifact eval/peti_check/<approved-run>.json
```

## 4. Enablement rule

Keep `PETI_CHECK_ENABLED=false` and public species/modality capability flags
off until the evidence bundle, manual review, release decision JSON, and
operator sign-off are archived together. Audio remains independently gated.
