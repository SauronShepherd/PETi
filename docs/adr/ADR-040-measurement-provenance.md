# ADR-040 — Measurement provenance is explicit

Phase 6 stores every measurement with an explicit source class: `MEASURED`,
`DOCUMENTED`, `OWNER_REPORTED`, or `AI_ESTIMATED`. Client-created records may
not use `AI_ESTIMATED`. Timeline and measurement responses preserve that class
so display and trend filters cannot silently convert estimates into measured
facts.
