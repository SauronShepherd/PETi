# Reconciliation Contract

Reconciliation domains include analysis, funding, rewards, billing, reports, deletion and notifications. Every reconciler is bounded, idempotent, payload-free in logs and reports unresolved work explicitly.

The shared implementation is `backend/app/operations/reconciliation.py`.
Adapters call `OperationsService.reconcile(domain, operation_key, action)`;
completed keys are replay-safe, while unresolved identifiers remain `PENDING`.
The service stores statuses and identifiers only; domain payloads stay in their
canonical stores. Supported domains are `analysis`, `funding`, `reward`,
`billing`, `report`, `deletion`, and `notification`.
