# Phase 8 — Dog Initial Scan

Implemented surfaces:

- DOG-only capability with release flag and independently gated candidate fields.
- Guided capture metadata for face, full-body, optional standing/top/marking views.
- `DogInitialScanResultV1` prompt/schema artifacts with GOOD/PARTIAL/INSUFFICIENT evidence states.
- Candidate-only profile suggestions with source provenance and explicit Confirm/Correct/Reject/Skip review.
- Server-side rejection of exact age, exact weight, neuter/spay, ancestry, identity, and health claims.
- Funding provenance records `AI_PHOTO_STANDARD`; existing results and candidate review are not re-funded.
- API, deletion, ownership, idempotency, and Android review entry points.

No canonical pet profile mutation occurs in the specialist service.
