# Weekly Report evaluation manifest

Each split contains a JSON object with `manifest_version` and `cases`. A case
contains a deterministic `timeline`, `measurements`, `facts`, and expected
`gates`. The evaluator checks source traceability, provenance preservation,
stable-vs-insufficient semantics, and absence of unsupported clinical claims.

The fixtures intentionally contain synthetic identifiers and no customer data.
