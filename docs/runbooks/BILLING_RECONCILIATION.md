# Billing reconciliation runbook

Reconcile Play purchase, RTDN, and periodic records through one idempotency key
per purchase token/event. Never grant entitlement from a client-only status.
Quarantine unknown states, record the product/package mismatch, and retry only
after the publisher verification response is available.
