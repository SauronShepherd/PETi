# Phase 7 implementation status — Veterinary Record Vault

Implemented surfaces:

- private veterinary document metadata backed by Phase-3 media;
- owner/pet-scoped Record CRUD and short-lived authorized source access;
- candidate extraction boundary with immutable prompt/schema artifacts;
- `PENDING_REVIEW` candidate facts with source anchors and confidence labels;
- idempotent terminal review behavior for Confirm, Correct, and Reject;
- review audit records and source-traceable `DOCUMENTED` facts;
- documented weight/temperature bridge to Phase-6 measurements while
  preserving original value and unit;
- reviewed documented-fact Timeline projections;
- deletion preview and explicit dependent-fact deletion handling;
- Android Records panel and document picker using the canonical upload flow;
- local Android Records state persists across repository recreation, remains
  pet-scoped, and supports local candidate review actions;
- no advertising entry points for ordinary Record Vault use.
- authenticated local/worker extraction task boundary; public extraction
  requests cannot bypass Phase-2 funding or worker authentication;

Extraction remains candidate-only at the service boundary. A production worker
must supply a validated `DocumentExtractionV1` result after the generic
`AI_DOCUMENT_EXTRACTION` Phase-2 funding flow; this module intentionally never
silently promotes extraction output into clinical truth.

Local verification now includes dedicated Record Vault tests covering
candidate-only local extraction, review promotion, owner-scoped source access,
repeated-extraction idempotency, and the complete backend suite. Production OCR/VLM extraction remains
candidate-only by design and requires the cloud worker/provider boundary.

The local API E2E path is also covered: Floci media upload/finalization, Record
Vault creation, fixture extraction, candidate confirmation, documented
measurement projection, dependency-protected deletion, and source cleanup.
The worker path is covered with valid and invalid task identities.

The repeatable local acceptance command is:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test-floci-phase7.ps1
```

It starts the Floci container and runs the Phase 7 backend E2E with local
Firestore/Storage adapters and FakeAI; it does not contact GCP or paid
providers.
