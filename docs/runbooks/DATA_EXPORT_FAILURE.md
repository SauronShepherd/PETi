# Data export failure runbook

Keep the export request resumable and idempotent. Verify that every canonical
domain is enumerated with provenance; never return a partial export as complete.
Retry transient storage failures and surface a stable support reference.
