# Rollback Package

This is the operator checklist for a reversible PETi release. It is deliberately
fail-closed: a rollback is not considered complete until the exact revision,
configuration snapshot, and post-rollback probes are recorded.

## Inputs to freeze before deployment

- Git commit and container image digest.
- Cloud Run API and worker revisions, traffic split, min/max instances, and
  queue names.
- Provider/model, prompt, schema, guardrail, and feature-flag versions.
- Firestore index revision, migration status, and Secret Manager version IDs
  (IDs only; never copy secret values into this package).
- Current `release/EVIDENCE_MANIFEST.json` and `release/PRODUCTION_CONFIG_SNAPSHOT.json`.

## Stop conditions

1. Disable new analysis dispatch at the server-side AI kill switch.
2. Stop or pause new expensive queue work; do not delete canonical media or
   completed results.
3. Keep authenticated historical reads and privacy deletion available.
4. Preserve the correlation ID and deployment revision for every operator action.

## Rollback procedure

1. Confirm the incident, affected revision, and owner in the incident log.
2. Route API and worker traffic to the last known-good immutable revision.
3. Restore the previously recorded provider/model/prompt/schema/guardrail
   configuration as a single versioned set; never mix versions.
4. Reconcile queued jobs and billing events idempotently after the worker is
   healthy. Do not replay an event without its original idempotency key.
5. Verify `/health/live`, `/health/ready`, authenticated historical reads,
   deletion-status reads, and that new analysis remains blocked until explicitly
   re-enabled.
6. Capture the image digest, revision names, flag state, probe results, and
   rollback timestamp in the release evidence artifact.

## Recovery / re-enable criteria

Re-enable new work only after the provider, queue, funding, privacy residual,
and customer-SLO checks are green for the exact restored configuration. If any
check is missing, leave the kill switch enabled and keep the release NO-GO.

## External execution gate

This source procedure is complete, but the real Cloud Run traffic switch,
Cloud Tasks pause/replay, Secret Manager rollback, and post-rollback probes
still require a provisioned staging/production GCP project and operator
evidence. Source text alone must not be treated as a completed drill.
