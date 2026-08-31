# ADR: hackathon multi-agent web surface

## Decision

The canonical PETi contracts remain client-neutral. For the hackathon, the
existing `web/` client is the judge-facing adapter while the backend implements
the durable agent boundary. The public preview is simulated and must never be
presented as proof of backend execution.

## Context

The canonical product documents describe Native Android as the primary client,
but this repository currently exposes a web client. Replacing that baseline
silently would create specification drift.

## Consequences

- The golden path is implemented and demonstrated through `web/`.
- Android parity is explicitly future work, not claimed as complete.
- Backend ownership, safety, provenance, persistence and approval rules apply
  equally to future clients.
