# Phases 8–11 implementation status

Added the shared specialist capability boundary for:

- `DOG_INITIAL_SCAN`
- `DOG_DENTAL_CHECK`
- `DOG_FECES_CHECK`
- `DOG_BODY_CHECK`

The implementation is owner-scoped, dog-only, media-owned by Phase 3, and
provenance-bearing. Specialist results remain dedicated analysis types and do
not reuse PETi Check semantics. Initial Scan fields are candidates requiring
Confirm, Correct, Reject, or Skip; forbidden exact age, exact weight,
neuter/spay, ancestry, diagnosis, and hidden-disease claims are excluded.
Dental, feces, and body result payloads carry evidence-quality, uncertainty,
limitation, recommendation, and guardrail fields. Body comparisons return an
explicit compatibility state and never rewrite historical results.

Specialist submissions carry server-created Phase-2 reservation IDs, consume
once at the provider boundary, record exemption or credit provenance, and
retry idempotently without a second reservation. Android exposes explicit
funding-quote, reservation, and opt-in rewarded-funding actions.

Specialist jobs without a provider result remain `QUEUED` and complete through
the authenticated specialist worker boundary; pre-provider deletion releases
reserved funding.

Public backend surfaces added:

```text
POST /v1/pets/{pet_id}/initial-scans
GET  /v1/initial-scans/{scan_id}
GET  /v1/pets/{pet_id}/initial-scans
GET  /v1/initial-scans/{scan_id}/candidates
POST /v1/initial-scan-candidates/{id}/confirm
POST /v1/initial-scan-candidates/{id}/correct
POST /v1/initial-scan-candidates/{id}/reject
POST /v1/initial-scan-candidates/{id}/skip
POST /v1/pets/{pet_id}/dental-checks
GET  /v1/dental-checks/{check_id}
GET  /v1/pets/{pet_id}/dental-checks
POST /v1/pets/{pet_id}/feces-checks
GET  /v1/feces-checks/{check_id}
GET  /v1/pets/{pet_id}/feces-checks
POST /v1/pets/{pet_id}/body-checks
GET  /v1/body-checks/{check_id}
GET  /v1/pets/{pet_id}/body-checks
GET  /v1/body-checks/{check_id}/comparison
```

Current verification superseding this historical note: the backend suite has 266 passing tests, Ruff/mypy and the root quality gate pass, and Android build/lint/unit verification passes with the documented Windows JVM workaround. Real Gemini/device release certification remains external and intentionally pending.
