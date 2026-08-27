# PETi human-validation handoff

Status: `READY_FOR_HUMAN_EXECUTION_EXTERNAL_EVIDENCE_PENDING`
Scope: free hackathon/demo release; Premium and Google Play Billing are excluded.

## Entry criteria

Before testing begins, record the exact source snapshot, RC manifest hash,
Android artifact hash, API/worker revisions, model and prompt/schema/guardrail
versions, sanitized tester identity, and device details.

The automated entry gates are `pytest -q backend/tests`, Ruff, release-manifest
validation, traceability validation, `scripts/check.ps1`, Android unit/lint
checks, production-config validation, and scope-guard validation.

## Human execution matrix

Record one row per scenario with result, tester, timestamp, build/device,
evidence path, defect ID and retest result.

| Area | Required scenarios | Pass condition |
|---|---|---|
| Authentication | first launch, valid/invalid sign-in, expiry, sign-out, account switch, restart, offline, retry | no stale or cross-account data |
| Pet and records | create, edit/correct, partial date, timeline, delete, restore/reject restore | ownership, dates and lifecycle states are correct |
| Media | camera permissions, capture, rotation, retake, Photo Picker, SAF PDF, cancel, retry, process death | no crash, duplicate, leakage or upload without consent |
| PETi Check | submit, loading, result, uncertainty, urgent result, failure | observation-only language and deterministic safety |
| Specialists | demo flows, pending review, reject/reconfirm, wrong pet | correct review state, provenance and scope |
| Reports/history | report generation, insufficient source, urgent source, grounded question | sources remain intact; no unsupported claims |
| Collaboration | invitation, wrong invitee, expiry, accept, revoke, account switch | caregiver access remains pet-scoped |
| Notifications/deep links | permission states, foreground/background/cold start, invalid/expired/unauthorized links | no sensitive preview or unauthorized navigation |
| Privacy | export, deletion, pending state, completion/restart | authorized data only; deletion is understandable |
| Accessibility | TalkBack, focus, labels, contrast, text scaling, touch targets, announcements | no blocking accessibility defect |

Execute the matrix on low-resource, mainstream and recent devices, including
portrait/landscape, light/dark theme, slow/intermittent network, offline mode,
low storage, battery saver and background/foreground transitions.

## Stop conditions

Mark `NO-GO` or `PENDING_EXTERNAL_*` for cross-account exposure, unsafe medical
claims, deletion residuals, credential/token leakage, duplicate charges or
actions, unbounded retries, critical crashes, failed rollback, unexplained
cost, accessibility blockers, or RC identity mismatch.

## Scope and sign-off

Do not claim Premium/Play, production, legal approval, complete provider or
specialist certification, or device certification beyond executed evidence.
Human acceptance is complete only when every in-scope row has evidence, all
defects have a disposition, accessibility and privacy/legal reviews are signed,
and the final go/no-go decision is recorded without promoting unexecuted gates.
