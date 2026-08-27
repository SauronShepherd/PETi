# PETi architecture invariants

- AI inference is cloud-only; Android performs deterministic input handling only.
- Android never calls Gemini or contains Gemini credentials. The future provider belongs under `backend/app/ai/providers/`.
- Cloud systems are authoritative for identity, pets, credits, funding, media, analyses, safety, and records.
- Cloud Credits are server-authoritative and costly operations pass through funding.
- Advertising is isolated to funding flows; there is no ambient advertising.
- Media is private, owner-scoped, and finalized by backend storage verification.
- AI media provenance is server-authoritative: a `MediaAsset` ID is resolved by
  `MediaService` to its validated private bucket/object and MIME; clients and
  tasks never provide provider-ready URIs or file contents. Vertex transports
  use private `gs://`/`fileData` or SDK `Part.from_uri` parts, while the AI
  Studio API-key transport accepts only controlled inline data and fails closed
  otherwise. Providers do not create GCS clients.
- Android never chooses authoritative media object paths or retention policy.
- Media upload retries are idempotent and media deletion never requires credits.
- Safety is an independent pipeline stage after validation and guardrails.
- Species are registry-friendly string codes and fail closed without a released capability pack.
- The discarded local-AI architecture is obsolete and must not be reintroduced.
- LOCAL, DEV, STAGING, and PRODUCTION are isolated; production is never an implicit fallback.

# Phase 6 invariants

- Timeline is a deterministic projection over canonical measurements, Care
  occurrences, and stored PETi Check results; it is not a duplicate event
  store.
- Measurement provenance and original source units are immutable history
  fields; deterministic normalization never rewrites the source value.
- Client flows cannot create `AI_ESTIMATED` measurements, and smartphone core
  temperature measurement is not a supported route.
- Care and occurrences remain canonical when notification permission is denied,
  quiet hours suppress delivery, or a provider delivery fails.
- FCM payloads contain only opaque occurrence routing data; tokens, notes,
  measurements, and AI narratives are never logged or pushed.
- LOCAL fake FCM delivery is isolated from non-LOCAL Firebase Admin delivery.

# Phase 7 invariants

- Veterinary documents reuse private Phase-3 `DOCUMENT_SOURCE` media with
  `CLINICAL_DOCUMENT` retention and short-lived authorized reads.
- Document extraction creates owner-scoped pending candidates only; Confirm or
  Correct is required before a `DOCUMENTED` fact exists, while Reject never
  projects to Timeline.
- Source anchors, original values, original units, partial-date precision, and
  review action remain attached to every accepted documented fact.
- Documented weight and temperature projections retain `source_class=DOCUMENTED`
  and never overwrite measured history; conflicting source documents coexist.
- Deleting a source document previews and explicitly handles dependent facts;
  ordinary viewing, metadata, and review actions never enter advertising.

# Phases 8–11 invariants

- Specialist capabilities have independent analysis types, schemas, prompts,
  guardrail versions, and safety policies; none is a PETi Check prompt alias.
- Specialist results are owner-scoped, dog-capability-scoped, immutable source
  records with source media and provider provenance.
- Initial Scan creates candidate profile suggestions only; exact age, exact
  weight, neuter/spay, genetic ancestry, identity, and health diagnosis are
  not inferred or silently written to pet profiles.
- Dental, feces, and Body Check results separate visible observations,
  uncertainty, evidence quality, limitations, and safety guidance. A visual
  result cannot claim hidden disease, treatment, or diagnostic certainty.
- Body longitudinal comparison is a versioned derived result and cannot rewrite
  historical analysis payloads or relabel measured/documented weights.
# Phase 2 economic invariants

- Backend-only credit authority; Android has no direct economic Firestore access.
- Ledger entries are immutable and grants preserve funding provenance.
- Cost profiles are versioned and remotely controlled.
- Reservation precedes costly execution; consume/release are idempotent.
- Advertising is opt-in and only reachable from an explicit funding flow.
