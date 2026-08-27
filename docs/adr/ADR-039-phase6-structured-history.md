# ADR-039 — Phase 6 structured history and reminder boundaries

## Decision

Timeline, measurements, Care items, occurrences, notification preferences and
device registrations are user-owned structured records. Timeline entries are
projections that retain a source entity ID; they are not an independent copy
of the source record.

Measurements retain the exact original value and unit and also store a
deterministic normalized value. Provenance is explicit. Client requests cannot
create `AI_ESTIMATED` records, and conflicting records coexist.

Care state is canonical independently of Android notification permission.
Notifications are a delivery channel only: dismissing a notification does not
complete or delete an occurrence.

## Consequences

Ordinary Phase 6 operations do not reserve credits, invoke Gemini, or require
advertising. Cached Android data must be discarded on account switch; writes
remain server-authoritative.
