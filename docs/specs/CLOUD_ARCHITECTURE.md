# PETi — Cloud Architecture Specification

**Version:** 1.0.0-cloud  
**Date:** 2026-08-12  
**Status:** Canonical system architecture  
**Architecture style:** Native Android client + cloud-authoritative modular backend + asynchronous AI workers

# 1. Architecture objective

The PETi architecture must optimize simultaneously for:

1. customer usefulness;
2. AI quality;
3. veterinary-safety boundaries;
4. privacy;
5. cost control;
6. clean user experience;
7. species extensibility;
8. operational simplicity;
9. testability;
10. server-authoritative economics.

The architecture intentionally does **not** optimize for offline AI.

---

# 2. System context

```text
┌─────────────────────────┐
│       PET OWNER         │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│    PETi Android App     │
│                         │
│ Compose / CameraX /     │
│ Picker / Care / Results │
└────────────┬────────────┘
             │ Firebase ID token
             │ HTTPS
             ▼
┌─────────────────────────┐
│      PETi Cloud API     │
│       Cloud Run         │
└─────┬──────┬──────┬────┘
      │      │      │
      │      │      └─────────────┐
      │      │                    │
      ▼      ▼                    ▼
 Firestore   GCS             Cloud Credit /
 metadata    private media    Funding Engine
      │      │                    │
      │      │                    ▼
      │      │              Rewarded Ad SSV
      │      │
      └──┬───┘
         │
         ▼
    Cloud Tasks
         │
         ▼
┌─────────────────────────┐
│  Private Analysis Worker│
│       Cloud Run         │
└────────────┬────────────┘
             │
             ├─ Media preparation
             ├─ Species/task policy
             ├─ Gemini adapter
             ├─ Schema validation
             ├─ Semantic guardrails
             └─ Safety engine
             │
             ▼
         Firestore
             │
             ▼
       Android result
```

---

# 3. Architectural authorities

| Domain | Authority |
|---|---|
| Identity | Firebase/Auth backend validation |
| Account role | PETi backend |
| Pet data | Firestore |
| Species capability | PETi backend |
| AI release state | PETi backend |
| User media | private GCS |
| AI jobs | backend/Firestore |
| AI result | backend/Firestore |
| Safety | deterministic backend engine |
| Cloud Credits | backend ledger |
| Rewarded-ad grant | server verification |
| Premium allowance | backend after Play reconciliation |
| Retention | backend |
| Android cache | non-authoritative |

---

# 4. Android architecture

```text
Compose UI
   │
ViewModel / StateFlow
   │
Use Cases
   │
Repositories
   │
PetiApiClient
   │
HTTPS
```

Platform adapters:

```text
Credential Manager
Firebase Auth
CameraX
Photo Picker
SAF
Media3
WorkManager
FCM
Crashlytics
Rewarded Ad SDK
```

Android must never invoke Gemini directly.

Android must never grant Cloud Credits.

Android must never authorize itself.

---

# 5. Backend logical architecture

The backend may deploy as a small number of Cloud Run artifacts while remaining logically modular.

```text
API
├── Identity/AuthZ
├── Pet Domain
├── Capability Registry
├── Funding/Credits
├── Advertising Verification
├── Billing
├── Upload Sessions
├── Records
├── Measurements
├── Care
├── Timeline
├── Reports
└── Operations

Worker
├── Media Preparation
├── Prompt Registry
├── Gemini Provider
├── Structured Output
├── Semantic Guardrails
├── Safety
├── Longitudinal Selection
└── Result Persistence
```

Avoid unnecessary microservices.

---

# 6. Expensive-operation funding architecture

This is a primary architecture boundary.

```text
User requests operation
        │
        ▼
Cost Resolver
        │
        ▼
Funding Resolver
        │
  ┌─────┼────────────────────┐
  │     │                    │
  ▼     ▼                    ▼
Free  Existing             Premium/
allowance credits          exempt
  │     │                    │
  └─────┴──────────┬─────────┘
                   │
             funded?
              │   │
             yes  no
              │   │
              │   ▼
              │  Offer rewarded ad
              │       │
              │       ▼
              │  user accepts?
              │   │       │
              │  no      yes
              │   │       │
              │   │       ▼
              │   │   Ad provider
              │   │       │
              │   │       ▼
              │   │   Server verification
              │   │       │
              │   │       ▼
              │   │   Grant credits
              │   │       │
              └───┴───────┘
                       │
                       ▼
                Atomic reservation
                       │
                       ▼
                  Execute operation
```

There is intentionally **no advertising path in ordinary navigation**.

---

# 7. Rewarded-ad trust boundary

Untrusted:

- Android “reward earned” callback;
- local client state;
- request parameters that claim credit.

Trusted only after validation:

- server-side provider verification;
- PETi-issued reward nonce;
- unique provider transaction;
- backend identity match.

Security invariant:

> A modified Android APK must not be able to mint Cloud Credits.

---

# 8. AI execution architecture

```text
Accepted AnalysisJob
        │
        ▼
Cloud Tasks
        │
        ▼
Private Worker
        │
        ├── Load pet/species
        ├── Resolve SpeciesCapabilityPack
        ├── Resolve task policy
        ├── Load approved historical context
        ├── Prepare media
        ├── Call Gemini
        ├── Parse structured result
        ├── Schema validate
        ├── Semantic validate
        ├── Apply safety
        ├── Persist result
        ├── Persist cost/provenance
        └── Notify completion
```

---

# 9. Species architecture

PETi is product-wide pet-agnostic but AI-specific.

```text
AnimalProfile
     │ species
     ▼
SpeciesCapabilityRegistry
     │
     ├── DOG v1
     │    ├── onboarding
     │    ├── generic visual
     │    ├── behavior
     │    ├── audio
     │    ├── dental
     │    ├── feces
     │    └── body
     │
     ├── CAT future
     ├── RABBIT future
     └── ...
```

Every pack owns or references:

- prompt policy;
- schema compatibility;
- terminology;
- safety rules;
- released feature set;
- evaluation evidence.

Unknown species never inherit dog configuration.

---

# 10. Safety architecture

Safety is deliberately separated from the language model.

```text
Gemini structured candidate
          │
          ▼
Schema validator
          │
          ▼
Semantic guardrails
          │
          ▼
Deterministic Safety Engine
          │
          ▼
Customer result
```

If Gemini and deterministic policy disagree, safety policy wins.

Advertising is downstream from this system and cannot modify it.

---

# 11. Provenance architecture

Every material AI result stores:

```text
analysis_id
animal_id
species
analysis_type
media_ids
prompt_version
schema_version
guardrail_version
safety_version
species_pack_version
media_preparation_version
provider
model
timestamps
usage
cost
```

Historical claims store links to contributing canonical records.

Hidden chain-of-thought is not stored or exposed.

---

# 12. Media architecture

## 12.1 Source media

Private GCS objects.

## 12.2 Metadata

Firestore.

## 12.3 Upload authorization

Short-lived and object-scoped.

## 12.4 Retention

Policy-driven asynchronous deletion.

## 12.5 Derived result

May outlive source media when policy allows.

This permits PETi to offer:

- low-cost transient source handling;
- optional longer retained storage funded by Cloud Credits;
- useful long-term structured history.

---

# 13. Cloud storage economics

Storage funding should not create an advertisement for every file.

Use thresholds and allowances.

Example conceptual model:

```text
Included retained-media allowance
            │
            ▼
      capacity remaining?
       │             │
      yes            no
       │             │
 retain normally   Offer:
                   - transient retention
                   - Cloud Credit
                   - Premium allowance
```

The exact allowance is remotely configurable.

---

# 14. Analysis economics

Every AI operation records actual provider/cloud usage where available.

Internal cost model:

```text
operation
   ├── AI inference cost
   ├── preprocessing compute
   ├── storage delta
   ├── network delta
   └── ancillary service cost
```

Funding model:

```text
FREE
REWARDED_AD
SPONSOR
PREMIUM
PROMOTION
INTERNAL
ADMIN
```

PETi therefore measures whether free usage is financially sustainable rather than assuming it.

---

# 15. Longitudinal architecture

Timeline source objects remain canonical.

A baseline/change operation does not rewrite its sources.

```text
Timeline sources
   │
   ▼
Compatibility filter
   │
   ▼
Sufficient evidence?
 │             │
no             yes
 │             │
 ▼             ▼
INSUFFICIENT   comparison
                │
                ▼
        stable / changed
```

Source deletion invalidates/recomputes dependent aggregates.

---

# 16. Veterinary Record Vault architecture

```text
SAF
 │
 ▼
private upload
 │
 ▼
source document
 │
 ├── viewer
 │
 └── optional AI extraction
       │
       ▼
 candidate facts
       │
   ┌───┼────┐
   ▼   ▼    ▼
Confirm Correct Reject
```

AI extraction may consume Cloud Credits.

Viewing an existing document does not.

---

# 17. Care architecture

Care data is canonical cloud data.

Notification delivery is a presentation channel.

```text
Reminder rule
   │
   ▼
Persistent occurrence
   │
   ├── Android in-app Care
   └── FCM notification
```

Notification denial never deletes the reminder.

---

# 18. Availability and failure design

## Cloud unavailable

PETi may show cached information.

Cost-bearing writes/AI operations are unavailable or safely queued only if the operation semantics support durable retry.

## Gemini unavailable

Job becomes retryable.

No duplicate credit consumption.

## Ad inventory unavailable

No operation is falsely funded.

The user may:

- use another credit source;
- retry later;
- use Premium;
- skip the operation.

## Reward callback duplicated

Idempotent grant.

## Cloud Task duplicated

Idempotent job execution.

## App killed during upload

WorkManager resumes/reconciles.

## App killed during analysis

Analysis continues server-side.

---

# 19. Privacy boundaries

The most sensitive cloud content includes:

- pet photos/videos/audio;
- veterinary documents;
- owner context;
- household background;
- human voices/faces;
- extracted records.

Architecture requirements:

- tenant isolation;
- private objects;
- minimal logs;
- minimal analytics;
- separate consent for research;
- retention/deletion automation;
- limited support access;
- no public clinical-document URLs.

---

# 20. Advertising privacy boundary

The rewarded-ad system needs only what is required to fund an operation.

It does not need access to:

- pet medical history;
- veterinary document contents;
- AI result narrative;
- raw pet media;
- Timeline.

The funding domain should therefore depend on:

```text
user_id
operation_cost_class
reward_intent
credit_amount
```

rather than the clinical/observation payload itself.

Future personalized sponsorship must be designed as a separate reviewed feature and must never alter PETi output.

---

# 21. Operational control plane

Server controls:

- global AI kill switch;
- per-species enablement;
- per-capability enablement;
- provider/model enablement;
- cost profiles;
- credit prices;
- free allowances;
- retention limits;
- rewarded credit amount;
- Premium allowances.

Unsafe AI can be disabled without an Android release.

---

# 22. Environment topology

Minimum:

```text
LOCAL
  Firebase emulators / fake services

DEV
  isolated cloud project

STAGING
  real Google Cloud services
  test users
  test ads
  real/fake Gemini depending test

PRODUCTION
  production Firebase/GCP
  production Gemini
  production rewarded ads
```

No production user content is copied into automated development environments.

---

# 23. Scalability

Scale first through managed Google Cloud primitives:

- Cloud Run autoscaling;
- Cloud Tasks backpressure;
- GCS object storage;
- Firestore indexing;
- concurrency caps;
- provider rate controls.

Do not introduce Kubernetes or unnecessary services without measured need.

---

# 24. Architectural invariants

The following must remain true:

1. No customer AI inference runs locally.
2. Android never owns authoritative credits.
3. Android never owns authoritative roles.
4. Android never directly holds Gemini credentials.
5. User media is private.
6. Reward grants are server-verified.
7. Ads do not appear during ordinary navigation.
8. Ads are optional funding for variable-cost operations.
9. Existing results never require ads to view.
10. Safety is independent of advertising.
11. Safety is independent of free-form Gemini wording.
12. Unsupported species fail closed.
13. Retry cannot double-consume credits.
14. Duplicate ad verification cannot double-grant credits.
15. Observations and provenance remain traceable.
16. Source measurements retain original units.
17. User-confirmed/documented facts outrank AI estimates.
18. Cloud cost is measured per operation.
19. Every AI capability has a server kill switch.
20. PETi remains useful without Premium.

---

# 25. Architecture Definition of Done

This architecture is considered implemented when:

- the Android application contains no active local AI inference stack;
- all canonical account/pet/result data survive reinstall through cloud persistence;
- one real Android → Cloud API → private media → Cloud Tasks → Gemini → validated result → Android path works;
- Cloud Credit funding is server-authoritative;
- rewarded-ad server verification grants reusable credits safely;
- no ambient advertising exists in customer navigation;
- private media authorization tests pass;
- duplicate reward/job delivery is harmless;
- AI safety gates operate independently from Gemini;
- species packs fail closed;
- cost and funding provenance is observable;
- AI/provider/capability kill switches work without an app release.