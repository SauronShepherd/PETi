# PETi — Detailed Build Plan

## Phase 0 — Environment and Engineering Foundation

**Version:** 1.0.0-cloud  
**Date:** 2026-08-12  
**Status:** Implementation Plan  
**Product:** PETi  
**Primary client:** Native Android  
**Backend:** Google Cloud  
**AI runtime:** Cloud-only  
**Commercial model:** Free-first, with opt-in rewarded advertising only for materially costly cloud operations; optional Premium

---

# 1. Phase 0 Objective

Phase 0 establishes a **new, clean, executable PETi repository** and all engineering boundaries required by the canonical PETi cloud specifications.

This phase is not intended to implement customer product features.

Its purpose is to ensure that all later PETi phases can be implemented in small, testable, deterministic increments without carrying forward obsolete architecture or unnecessary technical debt.

At the end of Phase 0, the following must work from a clean checkout:

```text
Android build
Android unit tests
Android lint
Android emulator smoke test

Backend startup
Backend unit tests
Backend lint
Backend type checks

Contract checks
Architecture checks
Secret checks

Root repository quality command
CI pipeline
```

The repository must have **zero dependency on the discarded local-AI architecture**.

---

# 2. Canonical Architecture Decisions

Before implementing product features, Codex must create:

```text
docs/ARCHITECTURE_INVARIANTS.md
```

The following invariants are mandatory.

---

## INV-001 — Cloud-only AI

PETi performs all AI inference through PETi-controlled cloud services.

Android must never perform PETi AI inference.

Explicitly forbidden:

```text
LiteRT
TensorFlow Lite PETi models
local VLM inference
local LLM inference
downloadable PETi AI models
local AI model registry
offline AI analysis
local/cloud AI parity logic
```

Android may perform deterministic technical work such as:

- MIME/type validation;
- file-size checks;
- duration checks;
- image orientation handling;
- basic compression;
- thumbnail generation;
- deterministic local input checks.

These operations must not become semantic PETi AI inference.

---

## INV-002 — Gemini is never called directly from Android

Forbidden architecture:

```text
Android
   ↓
Gemini
```

Required architecture:

```text
Android
   ↓
PETi Cloud API
   ↓
PETi Analysis Worker
   ↓
Gemini
```

No Gemini production credential may exist in:

- the APK;
- Android resources;
- Gradle properties committed to the repository;
- client-accessible configuration;
- release assets.

---

## INV-003 — Cloud data is canonical

Authoritative product state lives in PETi backend/cloud systems.

```text
users                → cloud
pet profiles         → cloud
species capabilities → cloud
credits              → cloud
funding decisions    → cloud
media metadata       → cloud
media bytes          → private cloud storage
analysis jobs        → cloud
analysis results     → cloud
timeline             → cloud
measurements         → cloud
care/reminders       → cloud
documents            → cloud
reports              → cloud
feature flags        → cloud
```

Android persistence is limited to:

- cache;
- UI state;
- pending local draft state;
- temporary upload state.

Android local data is never authoritative for:

- roles;
- ownership;
- Cloud Credit balance;
- entitlement;
- Premium state;
- reward completion;
- AI release state;
- safety.

---

## INV-004 — Cloud Credits are server-authoritative

Android must never grant itself Cloud Credits.

The backend owns:

```text
balance
grant
reservation
consumption
release
adjustment
funding provenance
```

Every future costly operation must depend on a backend funding decision.

---

## INV-005 — No ambient advertising

PETi must not contain:

```text
banner advertising
feed advertising
random interstitial advertising
automatic navigation advertising
Home advertising
Timeline advertising
Care advertising
result advertising
record-viewer advertising
```

Advertising exists only as a funding mechanism for materially costly cloud operations.

Required pattern:

```text
User requests costly operation
        ↓
Backend resolves funding
        ↓
Insufficient credits/allowance
        ↓
PETi explicitly offers rewarded ad
        ↓
User voluntarily accepts
        ↓
Rewarded ad
        ↓
Server verification
        ↓
Cloud Credits granted
        ↓
Operation may proceed
```

Ordinary PETi navigation should feel ad-free.

---

## INV-006 — Safety is independent from Gemini

Required future AI pipeline:

```text
Cloud media preparation
        ↓
Gemini candidate result
        ↓
Schema validation
        ↓
Semantic guardrails
        ↓
Deterministic Safety Engine
        ↓
Normalized PETi result
```

Gemini must not be the sole authority for urgency or safety routing.

---

## INV-007 — Species fail closed

PETi is a multi-species product at the domain level.

AI capabilities are species-specific.

Required rule:

```text
AnimalProfile.species
        ↓
SpeciesCapabilityPack
        ↓
Capability exists?
        ↓
Released?
        ↓
Allowed
```

Unknown or unsupported species must never silently use dog semantics.

---

## INV-008 — Costly operations are measurable

Every materially costly cloud operation must eventually support:

```text
operation_type
cost_class
funding_source
estimated_cost
actual_cost
credits_reserved
credits_consumed
```

Do not distribute arbitrary quota logic throughout Android or backend feature modules.

---

# 3. Create the Repository From Scratch

Codex must create a new repository structure:

```text
PETi/
├── android/
├── backend/
├── contracts/
├── eval/
├── infra/
├── scripts/
├── docs/
├── .gitignore
├── README.md
└── LICENSE
```

Do not copy the previous PETi application source tree.

Old PETi implementations may remain archived separately for reference, but they must not become dependencies of the new repository.

---

# 4. Android Project Bootstrap

Create:

```text
android/
├── app/
├── build-logic/
├── core/
│   ├── common/
│   ├── model/
│   ├── network/
│   ├── ui/
│   └── testing/
├── gradle/
├── build.gradle.kts
└── settings.gradle.kts
```

Do not create every future feature module during Phase 0.

Only establish modules necessary to enforce architecture boundaries and validate the development toolchain.

Recommended initial Gradle modules:

```text
:app
:core:common
:core:model
:core:network
:core:ui
:core:testing
```

Future feature modules are created only when their implementation phase begins.

---

# 5. Android Technology Baseline

Configure the project for:

```text
Kotlin
Jetpack Compose
Material 3
Navigation Compose
ViewModel
StateFlow
Kotlin Coroutines
Hilt
```

Phase 0 should not prematurely implement integrations such as:

```text
CameraX
Firebase Authentication
AdMob rewarded ads
Google Play Billing
Cloud Storage
Gemini
```

unless a minimal dependency is objectively required to validate project configuration.

---

# 6. Android Build Types

Create at minimum:

```text
debug
internal
release
```

## 6.1 `debug`

Purpose:

- local development;
- emulator development;
- fake services;
- local backend.

May use:

```text
LOCAL environment
FakeIdentityProvider
FakeAIProvider
Fake funding
```

when explicitly configured.

## 6.2 `internal`

Purpose:

- development/staging cloud testing;
- internal personas;
- fixture scenarios;
- test rewarded advertising later;
- diagnostics later.

Internal-only functionality must still require trusted server authorization.

## 6.3 `release`

Production customer build.

The release variant must eventually exclude:

```text
fixture media picker
fake authentication UI
fake advertising controls
fake billing controls
internal diagnostics
test scenario selectors
debug endpoints
```

Phase 0 must establish the build-variant mechanism even though most of these features do not exist yet.

---

# 7. Application Environment Abstraction

Create a typed environment model.

Conceptually:

```text
AppEnvironment
- LOCAL
- DEV
- STAGING
- PRODUCTION
```

Each environment resolves non-secret configuration such as:

```text
API base URL
logging level
debug tooling availability
fake-service availability
environment label
```

Do not hard-code production URLs directly inside screens or repositories.

Do not place secrets inside Android build configuration.

---

# 8. Android Application Shell

Create a minimal Compose application that launches successfully.

Phase 0 UI may display only:

```text
PETi

Environment: LOCAL
Backend: reachable / unavailable
```

This shell exists only to prove that:

```text
Compose works
Dependency injection works
Navigation works
Build variants work
Configuration works
Network client works
Unit testing works
Instrumentation testing works
```

Do not implement the final PETi Home screen during Phase 0.

---

# 9. Android State Architecture

Establish one standard pattern.

Recommended direction:

```text
Composable
   ↓ events
ViewModel
   ↓
Use Case / Repository
   ↓
Data Source / API
```

Repositories expose:

```text
Flow<T>
suspend functions
```

UI consumes immutable state.

Example:

```kotlin
data class ExampleUiState(
    val isLoading: Boolean = false,
    val data: ExampleData? = null,
    val error: UiError? = null,
)
```

Avoid:

- network calls from Composables;
- Firestore calls directly from screens;
- global mutable user-state singletons;
- domain state owned directly by UI widgets;
- business rules embedded in navigation code.

---

# 10. Backend Bootstrap

Create:

```text
backend/
├── app/
│   ├── main.py
│   ├── api/
│   ├── auth/
│   ├── config/
│   ├── domain/
│   ├── repositories/
│   ├── services/
│   ├── media/
│   ├── ai/
│   │   ├── providers/
│   │   ├── preparation/
│   │   ├── validation/
│   │   └── guardrails/
│   ├── safety/
│   ├── credits/
│   ├── advertising/
│   ├── billing/
│   ├── records/
│   ├── care/
│   ├── privacy/
│   └── operations/
├── tests/
├── pyproject.toml
└── README.md
```

Most packages may contain only interfaces, base models, documentation or placeholders during Phase 0.

Do not implement complete product domains prematurely.

---

# 11. Python Technical Baseline

Use:

```text
Python 3.13+
FastAPI
Pydantic v2
pytest
ruff
mypy
```

External integrations must be accessed through explicit interfaces/adapters.

Domain logic must not import Google Cloud SDKs directly unless that dependency belongs to the adapter layer.

---

# 12. Typed Backend Configuration

Create a typed settings model.

Conceptually:

```python
class Settings:
    environment: str
    project_id: str | None
    firestore_database: str | None
    media_bucket: str | None
    task_queue: str | None
    worker_url: str | None
```

Configuration sources:

```text
environment variables
Secret Manager in cloud environments
local fake configuration
```

Create:

```text
.env.example
```

The example file contains variable names and safe placeholders only.

Never commit:

```text
Gemini API keys
service-account JSON
Firebase private credentials
advertising verification secrets
Play purchase credentials
real signed URLs
```

---

# 13. Backend Health Endpoints

Implement:

```text
GET /health/live
GET /health/ready
```

## `/health/live`

Means:

> The service process is running.

## `/health/ready`

Means:

> The service has enough configured dependencies to accept its intended traffic.

Do not invoke Gemini as part of readiness checks.

The backend must start locally with the project's documented command, for example:

```bash
uvicorn app.main:app --reload
```

or a repository wrapper around it.

---

# 14. API Versioning

All public PETi APIs must start under:

```text
/v1/
```

Example future pattern:

```text
/v1/me
/v1/pets
/v1/credits
/v1/media
/v1/analyses
```

Do not begin with unversioned APIs and migrate later unnecessarily.

---

# 15. Standard API Error Contract

Define one customer-safe error structure.

Example:

```json
{
  "code": "PETI_ERROR_CODE",
  "message": "Customer-safe message",
  "correlation_id": "opaque-id",
  "retryable": false
}
```

Create typed backend exceptions such as:

```text
AuthenticationError
AuthorizationError
ValidationError
ResourceNotFoundError
ConflictError
FundingRequiredError
CapabilityUnavailableError
RetryableInfrastructureError
```

Never expose:

```text
Python stack traces
Firestore internals
Gemini raw errors
signed URLs
secrets
tokens
provider credentials
```

to Android clients.

---

# 16. Correlation IDs

Implement request correlation IDs during Phase 0.

Every API request receives:

```text
correlation_id
```

Future propagation path:

```text
Android request
     ↓
Cloud API
     ↓
Cloud Task
     ↓
AnalysisJob
     ↓
Worker
     ↓
Gemini provider call
     ↓
result/support diagnostics
```

Correlation IDs must contain no user-sensitive content.

---

# 17. Structured Logging

Configure structured backend logging from the start.

Supported fields should include:

```text
timestamp
environment
service
correlation_id
operation
status
duration_ms
```

Future logs may also include safe identifiers such as:

```text
analysis_id
media_id
operation_type
```

Never log ordinary sensitive content such as:

```text
raw photo/video/audio
veterinary document contents
full owner free text
Firebase tokens
Google credentials
signed URLs
Gemini secrets
```

Create a reusable redaction utility.

---

# 18. External-Service Interfaces

Establish ports/interfaces for future integrations.

Recommended interfaces include:

```text
IdentityProvider
UserRepository
AnimalRepository
SpeciesCapabilityRepository
MediaRepository
ObjectStorage
TaskQueue
AIProvider
CreditRepository
RewardVerifier
BillingGateway
NotificationGateway
Clock
IdGenerator
```

Phase 0 should provide fake implementations for the interfaces required by initial tests.

Future phases provide production implementations using:

```text
Firebase Authentication
Firestore
Cloud Storage
Cloud Tasks
Gemini
rewarded-ad server verification
Google Play Billing
FCM
```

---

# 19. Mandatory FakeAIProvider

Production PETi will use Gemini, but normal CI must not invoke a paid production model.

Create:

```text
AIProvider
```

and:

```text
FakeAIProvider
```

Initial scenarios:

```text
SUCCESS
TIMEOUT
RATE_LIMIT
MALFORMED_OUTPUT
SAFETY_VIOLATION
```

Phase 0 does not need the complete PETi Check result contract.

The goal is to establish a deterministic provider boundary.

---

# 20. Fake Clock

Create injectable time abstractions.

Backend:

```text
Clock
SystemClock
FakeClock
```

Android where useful:

```text
TimeProvider
SystemTimeProvider
FakeTimeProvider
```

Future functionality will depend on deterministic time for:

```text
credit expiry
reward intents
retention
reminders
weekly reports
idempotency
scheduled operations
```

Avoid embedding `now()` calls directly in domain logic.

---

# 21. ID Generation Abstraction

Create:

```text
IdGenerator
UuidGenerator
FakeIdGenerator
```

Use deterministic ID generation where it materially improves tests.

Future entities include:

```text
analysis jobs
media assets
Cloud Credit ledger entries
reward intents
correlation IDs
reports
```

---

# 22. Shared Contracts Directory

Create:

```text
contracts/
├── README.md
├── api/
├── analysis/
├── media/
├── credits/
└── species/
```

Do not create large speculative schemas.

Start only with stable foundational concepts already required by the canonical specifications.

---

# 23. Foundational Enums and Types

Create canonical representations for established concepts.

## User role

```text
CUSTOMER
INTERNAL_TEST
ADMIN
```

## Funding source

```text
FREE_ALLOWANCE
REWARDED_AD
SPONSOR
PREMIUM
PROMOTIONAL
INTERNAL_TEST
ADMIN_EXEMPT
```

## Media type

```text
IMAGE
VIDEO
AUDIO
DOCUMENT
```

## Credit ledger direction

```text
GRANT
RESERVE
CONSUME
RELEASE
ADJUST
```

Avoid prematurely defining every specialist AI enum.

---

# 24. Species Identifier Contract

The architecture must not encode DOG as the complete product domain.

Use a registry-friendly species code.

Conceptually:

```text
species_code: string
```

Dog will later be registered as:

```text
DOG
```

Avoid tightly coupling every domain layer to a compile-time enum that requires an Android release for every future supported species.

The backend species registry remains authoritative.

---

# 25. SpeciesCapabilityPack Skeleton

Create a basic domain contract.

Example:

```text
SpeciesCapabilityPack
- species
- version
- supported_analysis_types
- enabled_analysis_types
- safety_policy_version
- taxonomy_versions
- public_enabled
```

Phase 0 does not need real production capability packs.

Later phases will create:

```text
DOG v1
```

Architectural invariant:

```text
No capability pack
    ↓
No AI capability
```

---

# 26. AI Provider Abstraction

Define a generic AI boundary.

Conceptually:

```text
AIProvider.analyze(...)
```

Production implementation later:

```text
GeminiProvider implements AIProvider
```

Tests:

```text
FakeAIProvider implements AIProvider
```

Gemini-specific implementation details must not leak into Android or core product-domain logic.

---

# 27. Analysis Pipeline Skeleton

Create interfaces for:

```text
AnalysisOrchestrator
MediaPreparation
AIProvider
StructuredValidator
SemanticGuardrail
SafetyEngine
```

The orchestration order must be explicit:

```text
Prepare
   ↓
AI
   ↓
Structured validation
   ↓
Semantic guardrails
   ↓
Safety
   ↓
Persist
```

Create an automated test proving the standard orchestrator invokes stages in the expected order.

This becomes an architecture regression test.

---

# 28. Safety Abstraction

Create:

```text
SafetyEngine
```

Provide a deterministic fake/default Phase-0 implementation.

Do not implement safety inside `GeminiProvider`.

The architecture must make bypassing the safety layer difficult.

---

# 29. Cloud Credit Domain Skeleton

Create basic models for:

```text
CloudCreditAccount
CloudCreditLedgerEntry
CostProfile
FundingDecision
```

Example funding decisions:

```text
FUNDED
REWARDED_AD_REQUIRED
PREMIUM_OPTION
UNAVAILABLE
```

Do not implement real customer allowances in Phase 0.

Full Cloud Credit behavior belongs to Phase 2.

---

# 30. Advertising Isolation

Create the backend advertising boundary:

```text
backend/app/advertising/
```

The future Android advertising integration must live only inside a funding feature/boundary.

Do not create a global `AdManager` that can be injected into arbitrary screens.

Required architecture:

```text
ordinary PETi feature
        X
   advertising
```

Permitted architecture:

```text
costly operation
      ↓
funding flow
      ↓
rewarded advertising
```

---

# 31. Advertising Dependency Rule

Document and, where practical, automate the rule:

```text
feature-home       X→ advertising
feature-timeline   X→ advertising
feature-care       X→ advertising
feature-records    X→ advertising
feature-profile    X→ advertising

feature-funding     → advertising
```

Advertising must not become an ambient UI dependency.

---

# 32. No-Local-AI Dependency Gate

Create an automated repository check that fails if explicitly forbidden local PETi inference dependencies are introduced.

Inspect at minimum:

```text
Gradle dependencies
Android imports
repository dependency manifests
```

Initial banned categories should include the discarded PETi local inference stack.

The exact rule can evolve, but the purpose is permanent:

> A future implementation agent must not silently reintroduce local AI inference.

---

# 33. No-Gemini-in-Android Gate

Add an architecture check ensuring production Gemini client code belongs only under:

```text
backend/app/ai/providers/
```

and never under:

```text
android/
```

The check should also detect obvious committed Gemini credentials in Android configuration.

---

# 34. Secrets Hygiene

Configure `.gitignore` for:

```text
.env
local.properties
service-account JSON
keystores
credential caches
generated signed URLs
IDE secret files
local Firebase credentials
```

Create:

```text
docs/SECRETS.md
```

Canonical rule:

> Production secrets belong in Google Secret Manager or secure deployment configuration. Secrets must never be committed to the repository or embedded in the Android application.

Add secret scanning to CI where practical.

---

# 35. Local Development Environment

Local development must require no paid Gemini calls and no production advertising.

Target local architecture:

```text
Android emulator
      ↓
localhost PETi API
      ↓
fake repositories / local emulators
      ↓
FakeAIProvider
```

Firebase Emulator Suite may be prepared for later use where appropriate.

Local development must not depend on production cloud resources.

---

# 36. Environment Topology

Define:

```text
LOCAL
DEV
STAGING
PRODUCTION
```

## LOCAL

- fake/emulated;
- no paid Gemini;
- no real advertising;
- deterministic test services.

## DEV

- isolated development Google Cloud project;
- non-production data only;
- safe development integrations.

## STAGING

- production-like architecture;
- internal/test users;
- test rewarded advertising;
- controlled real Gemini evaluation where required.

## PRODUCTION

- real users;
- real Google Cloud services;
- production Gemini;
- production rewarded-ad verification;
- production data.

---

# 37. Environment Isolation

Prevent accidental cross-environment access.

Examples that must fail:

```text
LOCAL → production Firestore
DEV → production GCS bucket
STAGING → production customer data
unit test → production Gemini
debug app → production API unless explicitly approved
```

Configuration must never silently default to production.

Prefer startup failure to unsafe implicit fallback.

---

# 38. Infrastructure Directory

Create:

```text
infra/
├── README.md
├── local/
├── dev/
├── staging/
└── production/
```

Phase 0 does not need full production provisioning.

Document future required Google services:

```text
Firebase Authentication
Cloud Firestore
Cloud Storage
Cloud Run API
Cloud Run Worker
Cloud Tasks
Secret Manager
Cloud Logging
Cloud Monitoring
Cloud Scheduler
Firebase Cloud Messaging
```

---

# 39. Stable Root Developer Commands

Create repository-level commands such as:

```text
scripts/bootstrap
scripts/test
scripts/lint
scripts/check
scripts/run-backend
scripts/run-android-tests
```

The exact scripting language may be Bash or Python.

A new developer or coding agent should not need undocumented command sequences.

---

# 40. Backend Developer Commands

The following concepts must work:

```bash
cd backend
pytest
ruff check .
mypy app
```

and:

```bash
uvicorn app.main:app
```

or stable project wrappers.

---

# 41. Android Developer Commands

At minimum:

```bash
./gradlew assembleDebug
./gradlew test
./gradlew lint
```

Also establish a managed-emulator smoke-test task.

---

# 42. Root Quality Command

Create a single canonical command:

```bash
./scripts/check
```

It must execute all Phase-0 quality gates:

```text
contract checks
backend lint
backend type checks
backend unit tests
Android compilation
Android lint
Android unit tests
architecture checks
secret checks
```

Where practical, emulator smoke testing may be part of this command or a clearly defined CI extension.

---

# 43. Continuous Integration

CI must execute from a clean checkout.

Required logical pipeline:

```text
checkout
   ↓
setup JDK
setup Android SDK
setup Python
   ↓
restore/install dependencies
   ↓
contract checks
   ↓
backend lint/type/tests
   ↓
Android compile/lint/tests
   ↓
architecture checks
   ↓
secret checks
   ↓
build debug artifact
```

CI must not:

```text
call real Gemini
show real ads
require production credentials
access production data
```

---

# 44. Dependency Version Discipline

Dependencies must be reproducible.

Avoid:

```text
latest
*
unbounded >=
```

Critical SDK upgrades should be intentional changes with tests.

---

# 45. Formatting

Configure automated formatting rules for:

- Kotlin;
- Gradle Kotlin DSL;
- Python;
- Markdown where practical.

CI must consistently detect formatting drift.

Do not stack unnecessary overlapping formatting tools.

---

# 46. Static Analysis

## Android

Enable:

```text
Android lint
Kotlin compiler checks
```

## Backend

Enable:

```text
ruff
mypy
```

The goal is a small, understandable quality stack.

---

# 47. Test Structure

Android:

```text
src/test/
src/androidTest/
```

Backend:

```text
backend/tests/unit/
backend/tests/integration/
```

AI quality evaluation:

```text
eval/
```

Keep deterministic product tests separate from real Gemini evaluation.

---

# 48. Initial Backend Tests

Implement at least:

## Configuration tests

- LOCAL configuration loads.
- Missing mandatory PRODUCTION configuration fails closed.
- Secret values do not have unsafe defaults.

## API tests

- `/health/live` returns success.
- `/health/ready` returns the expected local state.
- unknown routes return customer-safe errors.
- correlation IDs are generated.

## Infrastructure abstraction tests

- `FakeClock` behaves deterministically.
- `FakeAIProvider` scenarios work.
- `FakeIdGenerator` is deterministic.

## Architecture tests

- analysis pipeline stage order is enforced;
- standard orchestration cannot skip safety.

---

# 49. Initial Android Unit Tests

Include:

- environment resolver;
- API base URL selection;
- basic ViewModel state;
- API error mapping;
- application bootstrap state.

---

# 50. Initial Android Instrumentation Test

A managed emulator must:

1. install the debug application;
2. launch PETi;
3. render the Phase-0 shell;
4. verify that the process does not crash;
5. verify the debug environment indicator;
6. optionally verify local backend health state when the test environment supports it.

This proves the instrumentation setup before product complexity is introduced.

---

# 51. Contract Validation Tests

Create basic contract validation for foundational schema/types.

Released contract versions must not be silently modified.

Future incompatible changes require:

- a new schema version;
- explicit migration or compatibility logic.

---

# 52. Codex Code-Ownership Boundaries

Future Codex implementation tasks must specify allowed areas.

Example:

```text
Allowed:
backend/app/credits/**
backend/tests/**

Do not modify:
android/**
backend/app/ai/**
```

Document this convention during Phase 0.

This reduces cross-feature accidental rewrites.

---

# 53. Standard Codex Task Format

Every future implementation task should follow a structure similar to:

```text
TASK
Implement <bounded capability>.

SOURCE CONTRACT
Relevant functional requirement.
Relevant technical requirement.
Relevant architecture invariant.

SCOPE
Permitted files/modules.

REQUIRED BEHAVIOR
Detailed expected behavior.

FAILURE BEHAVIOR
Required failure semantics.

TESTS
Tests that must be added or updated.

DO NOT
Explicit non-goals and forbidden modifications.

EXIT COMMAND
./scripts/check
```

Avoid broad prompts such as:

```text
Implement PETi authentication.
Build all onboarding.
Finish the backend.
```

---

# 54. Root README

Create a concise root `README.md`.

Recommended sections:

```text
PETi
Architecture summary
Prerequisites
Bootstrap
Run backend
Run Android
Run tests
Environment model
Repository structure
Architecture invariants
Canonical specifications
```

Do not turn the README into a duplicate of the full specifications.

---

# 55. Canonical Specifications Directory

Store the current PETi specifications under:

```text
docs/specs/
├── PETi_FUNCTIONAL_SPECIFICATION_v1.0.0-cloud.md
├── PETi_TECHNICAL_SPECIFICATION_v1.0.0-cloud.md
└── PETi_CLOUD_ARCHITECTURE_SPECIFICATION_v1.0.0-cloud.md
```

These files are the implementation authority.

Future product changes require explicit specification revision.

---

# 56. Architecture Decision Records

Create:

```text
docs/decisions/
```

Initial ADRs:

```text
ADR-001 Cloud-only AI
ADR-002 Cloud-authoritative persistence
ADR-003 Pet-generic domain with species-specific AI
ADR-004 Rewarded advertising only for costly cloud operations
ADR-005 Server-authoritative Cloud Credits
ADR-006 Safety independent of Gemini
ADR-007 No ambient advertising
```

Keep ADRs concise.

Their job is to prevent future architecture drift.

---

# 57. Obsolete Architecture Notice

Create:

```text
docs/OBSOLETE_ARCHITECTURE.md
```

Suggested content:

```text
The current PETi architecture does not use local AI inference.

Do not introduce:

- LiteRT PETi inference
- TensorFlow Lite PETi models
- local VLM/LLM analysis
- local model registry
- downloadable PETi specialist models
- offline PETi AI execution
- local/cloud inference parity logic

Cloud AI through the PETi backend is the only supported PETi inference architecture.
```

---

# 58. What Codex Must NOT Implement in Phase 0

Phase 0 must not expand into later product phases.

Do not implement yet:

```text
Google sign-in
real Firebase user identity
pet CRUD
real Firestore repositories
real Cloud Storage upload
Cloud Tasks
Gemini production provider
real rewarded advertising
real Cloud Credit business rules
Google Play Billing
Timeline
Care
Measurements
Veterinary Record Vault
Initial Scan
PETi Check
Dental Check
Feces Check
Body Check
Weekly Report
production deployment
```

Phase 0 builds the engineering foundation only.

---

# 59. Target Repository Shape at Phase-0 Completion

A healthy repository may resemble:

```text
PETi/
│
├── android/
│   ├── app/
│   ├── build-logic/
│   ├── core/
│   │   ├── common/
│   │   ├── model/
│   │   ├── network/
│   │   ├── ui/
│   │   └── testing/
│   ├── gradle/
│   ├── build.gradle.kts
│   └── settings.gradle.kts
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── config/
│   │   ├── domain/
│   │   ├── repositories/
│   │   ├── services/
│   │   ├── media/
│   │   ├── ai/
│   │   │   ├── providers/
│   │   │   ├── preparation/
│   │   │   ├── validation/
│   │   │   └── guardrails/
│   │   ├── safety/
│   │   ├── credits/
│   │   ├── advertising/
│   │   ├── billing/
│   │   ├── records/
│   │   ├── care/
│   │   ├── privacy/
│   │   └── operations/
│   ├── tests/
│   └── pyproject.toml
│
├── contracts/
│   ├── api/
│   ├── analysis/
│   ├── media/
│   ├── credits/
│   └── species/
│
├── eval/
│
├── infra/
│   ├── local/
│   ├── dev/
│   ├── staging/
│   └── production/
│
├── scripts/
│   ├── bootstrap
│   ├── check
│   ├── lint
│   ├── test
│   ├── run-backend
│   └── run-android-tests
│
├── docs/
│   ├── specs/
│   ├── decisions/
│   ├── ARCHITECTURE_INVARIANTS.md
│   ├── OBSOLETE_ARCHITECTURE.md
│   └── SECRETS.md
│
├── .gitignore
├── README.md
└── LICENSE
```

---

# 60. Phase 0 Acceptance Criteria

Phase 0 is complete only when every applicable item below is satisfied.

## Repository

- [ ] A new PETi repository exists.
- [ ] No previous PETi application source tree was copied in as the implementation base.
- [ ] Root repository structure matches the canonical architecture.
- [ ] The three cloud specifications are stored under `docs/specs/`.

## Android

- [ ] Android project builds from a clean checkout.
- [ ] `debug`, `internal`, and `release` build types exist.
- [ ] Compose application shell launches.
- [ ] Dependency injection works.
- [ ] environment abstraction exists.
- [ ] Android unit tests pass.
- [ ] Android lint passes.
- [ ] managed-emulator smoke test passes.
- [ ] no local PETi AI inference dependency exists.
- [ ] no Gemini production dependency exists in Android.

## Backend

- [ ] FastAPI backend starts locally.
- [ ] `/health/live` works.
- [ ] `/health/ready` works.
- [ ] backend unit tests pass.
- [ ] Ruff passes.
- [ ] Mypy passes.
- [ ] typed configuration exists.
- [ ] standard error contract exists.
- [ ] correlation IDs exist.
- [ ] structured logging exists.

## Architecture

- [ ] `AIProvider` abstraction exists.
- [ ] `FakeAIProvider` exists.
- [ ] `SafetyEngine` is a separate interface.
- [ ] analysis pipeline skeleton exists.
- [ ] architecture test verifies pipeline ordering.
- [ ] `CloudCreditAccount` domain skeleton exists.
- [ ] `CloudCreditLedgerEntry` domain skeleton exists.
- [ ] `FundingDecision` exists.
- [ ] `SpeciesCapabilityPack` skeleton exists.
- [ ] unsupported species behavior is designed to fail closed.
- [ ] advertising is isolated from ordinary UI architecture.
- [ ] no ambient-ad concept exists.
- [ ] local-AI architecture is explicitly marked obsolete.

## Testability

- [ ] Fake clock exists.
- [ ] deterministic ID generator exists.
- [ ] fake external-service boundaries are possible.
- [ ] normal CI requires no paid cloud service.
- [ ] normal CI makes no real Gemini call.
- [ ] normal CI shows no real advertisement.

## Security

- [ ] `.gitignore` protects credentials and secret material.
- [ ] `docs/SECRETS.md` exists.
- [ ] secret scanning exists where practical.
- [ ] no production credential is stored in source control.
- [ ] environment configuration fails closed instead of silently targeting production.

## Environments

- [ ] LOCAL is defined.
- [ ] DEV is defined.
- [ ] STAGING is defined.
- [ ] PRODUCTION is defined.
- [ ] environment isolation rules are documented.
- [ ] production is never the implicit fallback.

## Developer Experience

- [ ] root README exists.
- [ ] stable bootstrap command exists.
- [ ] stable backend run command exists.
- [ ] stable Android test command exists.
- [ ] root quality command exists.
- [ ] CI runs from a clean checkout.

---

# 61. Final Phase-0 Verification

Codex must finish Phase 0 by executing:

```bash
./scripts/check
```

The command must complete with:

```text
exit code 0
```

No acceptance criterion should be marked complete without corresponding executable evidence.

---

# 62. Phase 0 Exit Gate

Phase 0 is approved only when:

```text
Repository healthy
        +
Android shell executable
        +
Backend executable
        +
Tests deterministic
        +
CI green
        +
No production secrets
        +
No local AI
        +
No Android Gemini path
        +
No ambient advertising architecture
        +
Cloud Credit/funding boundaries established
        +
Species and safety boundaries established
```

Only after this gate passes should implementation move to:

# Phase 1 — Cloud Identity, Users, Pet Profiles and Species Registry

Phase 1 will introduce:

- Credential Manager;
- Firebase Authentication;
- server-side token verification;
- canonical PETi users;
- `CUSTOMER`, `INTERNAL_TEST`, and `ADMIN`;
- generic `AnimalProfile`;
- species registry;
- initial `DOG` capability registration;
- cloud-authoritative pet CRUD;
- selected-pet Android state;
- persistence/reinstall tests;
- cross-user authorization tests.

Phase 1 must not begin until Phase 0 is reproducibly green.
