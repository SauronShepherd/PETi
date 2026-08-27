# Firestore Failure Runbook

Fail closed for writes that could corrupt ownership, funding or deletion state. Existing cached/read-only results remain available where safe. Reconcile after recovery with idempotency keys and no raw pet-health logging.
