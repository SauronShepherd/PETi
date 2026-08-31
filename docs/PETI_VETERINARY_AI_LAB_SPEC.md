# PETi Veterinary AI Lab — Product and System Specification

Status: implementation baseline v1.0 · Audience: product, engineering, safety, operations and hackathon judges

## 1. Purpose

PETi Veterinary AI Lab is the mission-control layer for PETi's multi-agent veterinary support system. It makes every user-visible answer explainable as an operational trace without exposing private reasoning, measures whether users find the system useful, identifies frustration and safety concerns, and creates the evidence loop needed to improve agents, prompts, models and releases over time.

The Lab must never present PETi as a diagnostic veterinary device. It observes product and system behavior, supports human review, and preserves PETi's safety language and escalation boundaries.

## 2. Product outcomes

1. A pet owner can rate every eligible agent response as “helped” or “not quite”, select normalized reasons, optionally leave a bounded comment, revise or remove the rating, report a safety concern and later report an outcome.
2. An administrator can understand volume, completion, usefulness, grounding, safety, friction, performance, usage and model/agent attribution from a read-only Veterinary AI Lab.
3. An investigator can inspect a run as a timeline of plans, agents, steps, evidence counts, safety states, model calls, response publication and feedback, while never seeing hidden chain-of-thought.
4. A product team can compare releases using versioned metrics, confidence intervals, minimum-sample warnings, evaluation gates and explicit unknown states.
5. A privacy operator can export and erase owner-scoped Lab data and verify that no personal residue remains.
6. A hackathon viewer can replay clearly labelled synthetic Luna and Max scenarios without authentication or live backend dependency.

## 3. Actors and access

- Customer: may submit/read/update/remove only their own response feedback, safety reports and outcomes. No administrative metrics or traces.
- Internal tester: may access non-production Lab views only when explicitly enabled.
- Administrator: read-only aggregates, traces, models, feedback metadata, safety queues and audit. Viewing sensitive content requires a separate permission and mandatory audit.
- Reviewer: future mutable review workflow. P0 exposes the queue read-only.
- Scheduler/worker: service identities restricted to execution, rollup and retention endpoints.

All browser access to Firestore is denied. The FastAPI backend is the only authority.

## 4. User feedback experience

The feedback component appears after an eligible response and asks “¿Te ha ayudado?”. Positive and negative choices are keyboard-operable and expose pressed state. A choice reveals polarity-compatible reason codes and an optional 1,000-character comment. Submission shows a clear saved state and an edit control. Removal is explicit. Network failures retain the draft and permit retry.

Positive reasons: clear, answered question, useful next step, used evidence well, acknowledged limits, responsibly reassuring.

Negative reasons: not relevant, too generic, hard to understand, repetitive, missed evidence, incorrect interpretation, repeated context request, too slow, no clear next step, safety concern and other.

Demo mode stores feedback in session storage and performs no feedback network calls.

## 5. Mission Control information architecture

- Command Center: headline KPIs, confidence/preliminary labels, run state, activity, health and alerts.
- Live Runs and Run Inspector: filterable runs and deterministic trace timeline.
- Agent Laboratory: roster, version/capability/activity and outcome effectiveness.
- Model Intelligence: provider/model attribution, calls, known/unknown usage, latency and cost state.
- Evidence Lab: modality volume and grounded-claim metrics without media content.
- User Experience & Feedback: coverage, helpfulness, reasons and friction contributors.
- Safety & Evaluations: safety reports, human-review queue and critical release gates.
- Performance & Cost: latency, tokens, unknown usage and cost attribution.
- Health & Audit: freshness, write health, queue state and immutable administrative access history.

Every screen supports loading, empty, error, stale, preliminary and unknown states. Synthetic data is always labelled `SYNTHETIC_DEMO` and cannot be mixed with real metrics.

## 6. Trace model

Every interaction has `interaction_id`, `correlation_id`, environment, deployment revision and data classification. Agent execution records a run trace, ordered step traces and model-call traces. The canonical flow is plan → evidence intake → PETi Check specialist → safety review → care report → response publication. Each step records status, version, duration, evidence/claim counts, outcome and safety state where applicable.

Model traces include provider, model ID, prompt/schema/safety-policy versions, attempts, latency, token usage when reported, provider request ID and a sanitized error code. Missing usage is `UNKNOWN`, never zero. Provider prompts, raw model content and hidden reasoning are not telemetry.

Cloud Tasks redelivery must not duplicate a provider call. A transactional Firestore lease on the canonical run allows one worker to execute, rejects a concurrent valid lease and allows recovery after expiry.

## 7. Metrics

Metrics are versioned and retain numerator, denominator, sample count, value, 95% confidence interval where applicable and a preliminary flag. Missing feedback never counts as positive.

P0 includes run completion, feedback coverage, helpfulness, safe completion, grounded claim rate, unknown-usage coverage, latency, error rate, evidence counts and a bounded friction index. RUFS classifies useful, grounded, safe and overall as PASS, FAIL, UNKNOWN or NOT_ELIGIBLE. An overall pass requires all eligible dimensions to pass.

Hourly and daily materialized rollups avoid full collection scans. Allowed dimensions are environment, deployment, agent, provider/model, outcome and safety state. User, pet, run, response, request and comment identifiers are forbidden rollup dimensions.

## 8. Safety and human review

A customer safety report uses a closed category and severity enum. It creates an owner-scoped safety report and an internal review item. Optional description is isolated from analytical dimensions and ordinary admin lists. Critical administrative mutations and sensitive reads fail closed if their audit event cannot be persisted.

Critical gates cover dangerous under-triage, diagnosis language, fabricated measurement, medication guidance, false reassurance and schema validity. The P0 console is read-only; release promotion, rollback and kill-switch controls are not mutable until review permissions and gates are complete.

## 9. Privacy, security and retention

Raw owner identifiers are required only in owner-scoped operational records and are accompanied by HMAC pseudonyms. Telemetry properties use a closed allowlist and reject goals, prompts, comments, tokens, media content and free-form errors. Feedback comments are separately stored and omitted from ordinary public/admin payloads.

Owner export includes public response metadata, active feedback and outcome observations. It excludes prompts, internal costs, reviewer identity, comments, audit events and other users. Account deletion removes responses, feedback/comments, traces/model calls, safety reports, outcomes and owner-linked review assignments, then runs residual verification. Anonymous aggregate rollups and pseudonymous administrative audit remain only when they cannot reidentify the user.

Events and high-volume traces carry `expires_at`; comments have bounded retention; Terraform configures Firestore TTL. Audit and release records are retained under their separately approved policy.

## 10. APIs

Customer APIs:

- `PUT|GET|DELETE /v1/agent-runs/{run_id}/responses/{response_id}/feedback`
- `POST /v1/agent-runs/{run_id}/responses/{response_id}/safety-report`
- `POST /v1/agent-runs/{run_id}/outcomes`

Read-only Lab APIs under `/v1/internal/lab`: access, overview, runs/detail, agents, models, evidence metrics, feedback, safety/reviews, evaluations, performance, health and audit.

Private scheduled APIs: `/v1/internal/tasks/lab-rollup` and `/v1/internal/tasks/lab-retention`, authenticated by dedicated OIDC audience/service identity.

## 11. Demo and visual requirements

`/?demo=1#ADMIN` opens the Veterinary AI Lab using deterministic local fixtures. Luna demonstrates a useful grounded flow; Max demonstrates uncertainty, safety routing and actionable negative feedback. The UI uses a modern veterinary-laboratory visual language, remains readable at 390 px, supports reduced motion, and exposes semantic controls and visible focus.

No demo request may write to the backend. No demo record may be labelled real. The test suite captures desktop, tablet and mobile snapshots and checks navigation, run inspection and feedback behavior.

## 12. Operations and release gates

Feature flags independently control agent runtime, telemetry, feedback, admin, rollups and demo. Non-local Lab requires durable Firestore and a non-default HMAC secret. Rollup runs every ten minutes; retention runs daily. Monitoring covers telemetry failures, invalid events, rollup lag, feedback/admin errors and latency, queue age, duplicate prevention and provider cost anomalies.

A release passes only when backend unit/integration tests, type/lint checks, privacy/cardinality checks, contract validation, web static checks, Playwright demo tests, visual inspection, Terraform formatting/validation and data-invariant verification pass. Deployment remains flag-off by default and expands through DEV, staging and production canary with independent rollback switches.

## 13. Acceptance criteria

- No completed instrumented run lacks a response ID; failed runs have terminal traces.
- No concurrent/redelivered task can issue a second provider call while a valid lease exists.
- Feedback is owner-scoped, idempotent, polarity-valid, editable and removable.
- Safety reporting creates a review and a pseudonymous audit event.
- Admin/customer and production/non-production permission boundaries are tested.
- All metrics distinguish zero from unknown and show denominator/sample state.
- Owner export/deletion and residual verification cover every Lab personal entity.
- Browser Firestore rules remain fail-closed and infrastructure provisions indexes, TTL, secrets, schedulers and monitoring.
- Demo mode is deterministic, clearly synthetic, responsive and network-isolated.
- The complete automated gate passes from a clean checkout with documented deployment flags and rollback procedure.

The low-level implementation sequence and exact file-level plan are defined in [PETI_VETERINARY_AI_LAB_BUILD_PLAN.md](PETI_VETERINARY_AI_LAB_BUILD_PLAN.md).
