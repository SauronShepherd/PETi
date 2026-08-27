# ADR-031: Generic local AI platform behind a task boundary

Phase 4 local execution uses `FakeAIProvider` behind `AnalysisService` and `FakeTaskQueue`. Android submits only to the PETi API; it never contains a Gemini client. The worker route requires the local task identity header, while production adapters must use Cloud Tasks OIDC and server-only provider credentials.

The job state machine, ownership checks, READY-media checks, funding reservation boundary, provider-output validation, safety normalization, result provenance, and idempotency rules are shared by local and production implementations.
