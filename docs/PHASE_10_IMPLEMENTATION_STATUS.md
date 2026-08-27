# Phase 10 — Dog Feces Check

Implemented:

- DOG-only specialist route with release/public feature flags.
- Freshness, owner attribution, multi-dog, and hygiene guidance in the Android entry surface.
- Server-validated `FecesCaptureManifest` with freshness and producer confirmation before analysis.
- `FecesCheckResultV1` prompt/schema and controlled visible finding taxonomy.
- Visible-only guardrails for parasites, infection, occult blood, microbiome, internal-organ disease, dehydration, etiology, temperature, and treatment.
- Deterministic safety states for dark/tarry appearance, fresh-red-blood-like appearance, collapse, inability to keep water down, vomiting, and lethargy context.
- Owner context provenance is separated from image observations.
- Optional fail-closed comparison endpoint is exposed without claiming medical change.
- Funding provenance records `AI_SPECIALIST_STANDARD`; history and result access are not re-funded or advertised.

No laboratory or local feces model is introduced.
