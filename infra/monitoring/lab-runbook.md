# PETi Veterinary AI Lab runbook

## Alert triage

1. Confirm environment, deployment revision and whether the affected feature flag is enabled.
2. For telemetry failures, inspect sanitized error codes and Firestore quota/permission health. Never paste prompts, comments, media or tokens into tickets.
3. For rollup lag, verify the Scheduler OIDC audience, the latest `metric_rollups` bucket and raw-event freshness. Re-run the idempotent rollup task only after identity is verified.
4. For feedback 5xx, preserve customer ownership semantics. Disable `PETI_LAB_FEEDBACK_ENABLED` independently if writes are unsafe; response delivery must continue.
5. For queue age or duplicate prevention anomalies, inspect run state and lease expiry. Do not clear a live lease. Expired leases recover through normal redelivery.
6. For model cost/latency anomalies, disable the affected provider/model flag or agent runtime. Do not promote a challenger while a critical safety gate is failing.

## Privacy incident

Disable telemetry and feedback independently, preserve immutable audit, run `verify_lab_data.py`, execute owner deletion through the canonical privacy workflow, and use residual verification. Never query or export feedback comments into an operational dashboard.

## Rollback

Set Lab flags off in this order when necessary: feedback/admin, rollups, telemetry, then agent runtime. Restore the previous web artifact and backend revision. Existing traces remain readable according to retention policy; do not delete them as part of an ordinary rollback.
