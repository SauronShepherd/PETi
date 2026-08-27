# PETi — Technical Specification

**Version:** 1.0.0-cloud  
**Date:** 2026-08-12  
**Status:** Canonical technical baseline  
**Runtime:** Android client + Google Cloud backend + Gemini  
**AI model:** Cloud-only  
**Persistence authority:** Cloud  
**Funding authority:** Server-side PETi Cloud Credit ledger

# 1. Technical direction

PETi uses a native Android client connected to a cloud-authoritative backend.

The Android application is responsible for:

- user interaction;
- media capture/selection;
- lightweight deterministic input validation;
- upload orchestration;
- local transient caching;
- rendering server state;
- notifications/deep links.

The cloud is responsible for:

- identity authorization;
- canonical pet/account data;
- media ownership;
- storage;
- AI preprocessing;
- Gemini invocation;
- structured-output validation;
- semantic guardrails;
- safety;
- Timeline aggregation;
- longitudinal computation;
- report generation;
- credits/funding;
- advertisement reward verification;
- Premium reconciliation;
- feature flags;
- retention;
- operational controls.

No customer AI model executes on Android.

---

# 2. Recommended technology stack

## Android

- Kotlin;
- Jetpack Compose;
- Material 3;
- Navigation Compose;
- ViewModel;
- StateFlow;
- Kotlin Coroutines;
- Hilt;
- Credential Manager;
- Firebase Authentication;
- CameraX;
- Android Photo Picker;
- Storage Access Framework;
- Media3 where needed;
- WorkManager for resilient upload/status work;
- Firebase Cloud Messaging;
- Firebase Crashlytics;
- small encrypted/local cache only where justified.

## Backend

- Python;
- FastAPI;
- Pydantic v2;
- Cloud Run API service;
- private Cloud Run worker service;
- Cloud Tasks;
- Firestore;
- private Google Cloud Storage;
- Secret Manager;
- Cloud Scheduler;
- Cloud Logging;
- Cloud Monitoring.

## AI

- Gemini multimodal models through a server-side provider adapter;
- strict JSON/structured contracts;
- immutable prompt versions;
- media-preparation versions;
- deterministic semantic validators;
- provider-independent safety engine.

## Advertising

- rewarded-ad Android SDK;
- server-side reward-verification endpoint;
- signed reward/custom-data correlation;
- idempotent credit issuance.

## Optional Premium

- Google Play Billing;
- backend purchase verification/reconciliation;
- server-derived Premium allowance.

---

# 3. Repository structure

```text
/
  android/
    app/
    core/
    core-network/
    core-auth/
    core-media/
    core-ui/
    core-testing/
    feature-home/
    feature-pets/
    feature-analyze/
    feature-timeline/
    feature-care/
    feature-records/
    feature-measurements/
    feature-dental/
    feature-feces/
    feature-body/
    feature-settings/
    feature-funding/

  backend/
    app/
      api/
      auth/
      domain/
      repositories/
      services/
      media/
      ai/
        providers/
        prompts/
        preparation/
        validation/
        guardrails/
        evaluation/
      safety/
      credits/
      advertising/
      billing/
      longitudinal/
      reports/
      records/
      care/
      privacy/
      operations/
    tests/

  contracts/
  eval/
  infra/
  scripts/
  docs/
```

Obsolete local-model code should not remain in active dependency graphs.

---

# 4. Canonical data authority

| Concern | Authority |
|---|---|
| Account | backend / Firebase identity |
| Pet profiles | Firestore |
| Entitlements | backend |
| Cloud Credits | backend ledger |
| Rewarded-ad reward | backend verification |
| Media metadata | Firestore |
| Media/document bytes | private Cloud Storage |
| Analysis jobs | Firestore |
| AI result | Firestore |
| Safety state | backend |
| Timeline | backend canonical records |
| Measurements | Firestore |
| Care/reminders | Firestore |
| Weekly Reports | Firestore |
| Feature/capability state | backend configuration |
| Android local data | cache / pending client state only |

Local state is never authoritative for quota, credits, roles or safety.

---

# 5. Core domain objects

## User

```text
User
- id
- firebase_uid
- role
- billing_exempt
- ads_exempt
- created_at
- deleted_at
```

## AnimalProfile

```text
AnimalProfile
- id
- owner_user_id
- species
- display_name
- avatar_media_id
- profile_facts[]
- active_state
- created_at
- updated_at
```

## SpeciesCapabilityPack

```text
SpeciesCapabilityPack
- species
- version
- supported_analysis_types[]
- enabled_analysis_types[]
- taxonomy_versions
- safety_policy_version
- prompt_policy_versions
- evaluation_certificate_ids[]
- public_enabled
```

## MediaAsset

```text
MediaAsset
- id
- owner_user_id
- animal_id
- media_type
- purpose
- mime_type
- size_bytes
- duration_ms
- checksum_sha256
- storage_object
- retention_class
- status
- created_at
- delete_after
```

## AnalysisJob

```text
AnalysisJob
- id
- owner_user_id
- animal_id
- species
- analysis_type
- status
- media_asset_ids[]
- user_context
- idempotency_key
- funding_reservation_id
- species_pack_version
- prompt_version
- guardrail_version
- schema_version
- media_preparation_version
- provider
- provider_model
- attempts
- timestamps
```

## AnalysisResult

```text
AnalysisResult
- id
- job_id
- structured_payload
- evidence_quality
- safety_state
- validation_state
- provenance
- usage
- actual_cost
- created_at
```

## CloudCreditAccount

```text
CloudCreditAccount
- user_id
- available_balance
- reserved_balance
- updated_at
```

## CloudCreditLedgerEntry

```text
CloudCreditLedgerEntry
- id
- user_id
- amount
- direction: GRANT | RESERVE | CONSUME | RELEASE | ADJUST
- funding_source
- operation_type
- related_reward_id
- related_job_id
- idempotency_key
- created_at
```

## RewardedAdEvent

```text
RewardedAdEvent
- id
- user_id
- reward_nonce
- ad_provider
- expected_reward
- verification_state
- provider_transaction_id
- credit_grant_id
- created_at
- verified_at
```

## CostProfile

```text
CostProfile
- operation_type
- version
- credit_cost
- expected_cloud_cost_band
- max_media_size
- max_duration
- active
```

---

# 6. API surface

Representative API:

```text
GET    /v1/me
DELETE /v1/me

GET    /v1/pets
POST   /v1/pets
GET    /v1/pets/{pet_id}
PATCH  /v1/pets/{pet_id}
DELETE /v1/pets/{pet_id}

GET    /v1/species
GET    /v1/species/{species}/capabilities

GET    /v1/credits
GET    /v1/credits/costs
POST   /v1/credits/estimate

POST   /v1/ads/reward-intents
POST   /v1/ads/reward-verification
GET    /v1/ads/reward-intents/{id}

POST   /v1/media/upload-sessions
POST   /v1/media/{media_id}/finalize
PATCH  /v1/media/{media_id}/retention
DELETE /v1/media/{media_id}

POST   /v1/pets/{pet_id}/analyses
GET    /v1/analyses/{analysis_id}
GET    /v1/pets/{pet_id}/analyses

GET    /v1/pets/{pet_id}/timeline

GET    /v1/pets/{pet_id}/measurements
POST   /v1/pets/{pet_id}/measurements

GET    /v1/pets/{pet_id}/records
POST   /v1/pets/{pet_id}/documents
POST   /v1/documents/{document_id}/extract
POST   /v1/document-facts/{fact_id}/review

GET    /v1/pets/{pet_id}/reminders
POST   /v1/pets/{pet_id}/reminders

GET    /v1/pets/{pet_id}/reports

POST   /v1/billing/google-play/reconcile
```

Create operations use idempotency keys.

---

# 7. Cost-estimation and funding flow

Before a materially costly operation is submitted:

```text
1. Client sends operation metadata.
2. Backend resolves species/capability.
3. Backend calculates operation cost class.
4. Backend checks available funding.
5. Backend returns:
   FUNDED
   REWARDED_AD_AVAILABLE
   PREMIUM_OPTION
   TEMPORARILY_UNAVAILABLE
6. Client obtains funding where necessary.
7. Backend atomically reserves credits.
8. Job is accepted.
9. Credits are consumed only at the defined lifecycle boundary.
10. Failure before that boundary releases the reservation.
```

The lifecycle boundary must be explicit per operation.

For AI analysis, a recommended rule is:

- preflight rejection → release;
- upload failure → release;
- job never queued → release;
- accepted provider analysis → consume according to policy;
- infrastructure retry → no second consumption.

---

# 8. Rewarded-ad implementation

## 8.1 Reward intent

Before displaying an ad, Android requests a reward intent.

Backend creates:

```text
RewardIntent
- opaque id
- user id
- nonce
- reward amount
- expiry
- consumed=false
```

## 8.2 Android presentation

The Android client:

- displays the PETi funding explanation;
- requests the rewarded ad only after user acceptance;
- passes backend-issued opaque custom data if supported;
- never grants credits locally.

## 8.3 Server verification

The backend verifies the ad-provider callback.

Validation includes:

- signature/authenticity;
- reward-intent existence;
- expected user;
- nonce/custom data;
- expiry;
- provider transaction uniqueness;
- expected reward;
- replay protection.

## 8.4 Credit grant

Credit issuance is atomic and idempotent.

One provider transaction can create at most one reward grant.

## 8.5 Failure behavior

Unknown, invalid or replayed callbacks:

- create no credit;
- generate security telemetry;
- do not expose sensitive verification details to the client.

---

# 9. Media pipeline

Preferred flow:

```text
Android
  → request upload session
  → backend validates ownership/type/size
  → backend creates PENDING_UPLOAD MediaAsset
  → short-lived upload authorization
  → Android uploads directly to private GCS
  → finalize
  → backend verifies object metadata/checksum
  → READY
  → analysis submission
```

Large media should not pass through the public API process.

---

# 10. Cloud media preprocessing

Preprocessing happens in the worker/cloud environment.

Image:

- decode;
- orientation normalization;
- metadata minimization;
- dimension normalization;
- quality checks;
- model-ready representation.

Video:

- validate;
- inspect duration/codec;
- deterministic frame extraction;
- optional audio extraction;
- representative-frame selection;
- resolution/bitrate control;
- provider-specific preparation.

Audio:

- format validation;
- duration validation;
- normalization as needed;
- quality metadata.

Document:

- safe file validation;
- content-type verification;
- decompression/active-content protection;
- source preservation;
- extraction preparation.

Every analysis persists `media_preparation_version`.

---

# 11. Gemini provider abstraction

```text
MultimodalProvider.analyze(
    task,
    prepared_media,
    context,
    system_policy,
    prompt,
    response_schema,
    timeout
) -> ProviderResponse
```

Provider details do not leak into Android business logic.

The adapter records:

- provider;
- model;
- parameters;
- request identity;
- latency;
- usage;
- failure class.

Provider changes require evaluation before customer enablement.

---

# 12. Structured AI pipeline

```text
media/context
   ↓
task/species policy
   ↓
cloud preparation
   ↓
Gemini
   ↓
JSON parse
   ↓
schema validation
   ↓
semantic validation
   ↓
species-specific guardrails
   ↓
deterministic safety engine
   ↓
normalized result
   ↓
persistence
   ↓
Android
```

Free-form provider text is never trusted directly.

---

# 13. Safety boundary

The Safety Engine is independent of Gemini.

Inputs may include:

- normalized AI findings;
- owner context;
- measurements;
- selected confirmed records;
- species policy.

Safety output is authoritative.

Model-generated urgency can be treated as an input, never as the sole authority.

---

# 14. Species isolation

Every analysis requires:

```text
animal.species
→ SpeciesCapabilityPack
→ supported analysis?
→ released?
→ compatible prompt?
→ compatible schema?
→ compatible safety policy?
```

Failure is closed.

No fallback to dog semantics.

---

# 15. Longitudinal engine

Comparison selection is backend-controlled.

It may use only:

- same pet;
- same compatible analysis family;
- approved time window;
- compatible taxonomy/schema;
- approved historical fields/media.

The model never receives unrestricted account history.

---

# 16. Record Vault

Original veterinary documents are stored privately.

Derived extraction includes source anchors.

Material facts require explicit review before becoming confirmed record data.

Deleting a document follows deterministic dependency rules.

---

# 17. Storage and retention

Retention classes should include:

```text
TRANSIENT_ANALYSIS
RETAINED_ANALYSIS_MEDIA
PROFILE_MEDIA
CLINICAL_DOCUMENT
CONSENTED_EVALUATION
INTERNAL_FIXTURE
```

Retention execution is performed server-side.

User-facing retained-media allowance can be credit-funded without affecting structured-result retention.

---

# 18. Android caching

Android may cache:

- pet list;
- recent Timeline;
- result summaries;
- Care data;
- thumbnails where policy permits;
- pending forms.

Cache is disposable.

It is not canonical.

No local AI inference is permitted.

---

# 19. Authentication and authorization

Android obtains Firebase identity.

API verifies identity server-side.

Every resource operation verifies:

- authenticated user;
- ownership;
- role;
- species capability;
- funding entitlement where required.

Never trust:

- client role;
- client credit balance;
- client Premium flag;
- client reward completion;
- client pet ownership.

---

# 20. Security requirements

- no Gemini keys in APK;
- no GCP service credentials in APK;
- no public user-media bucket;
- signed/scoped upload/download access only;
- short-lived credentials;
- Secret Manager;
- least-privilege service accounts;
- customer endpoints cannot set ADMIN role;
- reward callbacks replay-protected;
- general logs exclude user content;
- analytics exclude raw pet-media content;
- document originals remain private;
- cross-user access tests are mandatory.

---

# 21. Observability

Track:

## Product

- operation requested;
- funding source;
- rewarded flow offered;
- rewarded flow accepted/canceled;
- credits granted;
- credits consumed;
- operation completed;
- operation failed.

## AI

- capability;
- species;
- model;
- prompt version;
- schema version;
- guardrail version;
- preparation version;
- latency;
- usage;
- actual cost;
- schema failure;
- semantic failure;
- abstention;
- safety state.

## Infrastructure

- API latency/errors;
- queue depth;
- worker failures;
- storage usage;
- egress;
- Firestore operations;
- Cloud Run CPU/memory;
- scheduled retention failures.

## Economics

- actual cloud cost per operation;
- AI cost per operation;
- advertising-funded credits;
- Premium-funded credits;
- sponsor-funded credits;
- cost per free active user;
- contribution per funding class.

---

# 22. Cost control

Every expensive workflow has:

- input caps;
- timeout;
- retry cap;
- concurrency limit;
- configured cost class;
- provider budget;
- media normalization strategy.

Global kill switches must exist for:

- all AI;
- individual species;
- individual capability;
- individual provider/model;
- rewarded-credit granting where necessary.

---

# 23. Testing strategy

Normal CI uses deterministic fakes for:

- authentication;
- Cloud Credit ledger;
- rewarded-ad verification;
- billing;
- media storage;
- Gemini;
- clock;
- notifications.

Real Gemini evaluation is separate.

Mandatory tests include:

- cross-user authorization;
- double reward callback;
- forged reward callback;
- duplicate Cloud Task;
- retry without double credit;
- insufficient credit;
- ad unavailable;
- canceled ad;
- preflight failure credit release;
- provider timeout;
- malformed provider output;
- schema-valid unsafe output;
- unsupported species;
- specialist safety violations;
- deletion;
- storage retention;
- process death/reconnect;
- Premium reconciliation.

---

# 24. Technical Definition of Done

The cloud architecture is complete only when:

- Android has no active local AI/runtime dependency;
- production AI keys exist only server-side;
- Firestore/GCS are canonical;
- reward verification is server-side;
- Cloud Credit reservation/consumption is atomic;
- retry/idempotency tests pass;
- media is private;
- AI output is validated structurally and semantically;
- safety is independent of provider output;
- species gating fails closed;
- cost metrics are recorded;
- production feature kill switches exist.