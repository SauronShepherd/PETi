# Report generation failure runbook

Inspect the week key, scheduler idempotency key, and source-reference counts.
Retry the generation job safely. Never replace an existing completed report;
write a new version only when the report version changes.
