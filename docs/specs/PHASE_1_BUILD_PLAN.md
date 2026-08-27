# PETi — Detailed Build Plan

## Phase 1 — Cloud Identity, Canonical Users, Pet Profiles and Species Registry

**Version:** 1.0.0-cloud  
**Date:** 2026-08-12  
**Status:** Codex Implementation Plan  
**Prerequisite:** Phase 0 completed with `./scripts/check` returning exit code `0`  
**Primary client:** Native Android  
**Backend:** FastAPI on Google Cloud architecture  
**Identity:** Google Sign-In through Android Credential Manager + Firebase Authentication  
**Canonical persistence:** Cloud Firestore behind the PETi backend  
**AI:** Not implemented in this phase  
**Advertising:** Not implemented in this phase  
**Cloud Credits:** Domain skeleton only; no business rules in this phase  
**Premium/Billing:** Not implemented in this phase

---

# 1. Phase 1 Objective

Phase 1 creates the first real PETi product domain.

At the end of this phase a real user must be able to:

1. launch the Android application;
2. sign in with a Google account;
3. obtain a Firebase-authenticated PETi session;
4. have a canonical PETi user created or restored in the backend;
5. retrieve the PETi species registry;
6. create one or more pet profiles using a generic `AnimalProfile` model;
7. list only their own pets;
8. open and edit one of their own pets;
9. delete one of their own pets;
10. select the active/current pet in Android;
11. close/relaunch the app and restore the same PETi account and pet data from the cloud;
12. reinstall/sign in again and recover the same cloud data;
13. sign out without another account's cached data becoming visible.

The phase must also establish:

- `CUSTOMER`, `INTERNAL_TEST`, and `ADMIN`;
- server-only trusted role assignment;
- `billing_exempt` and `ads_exempt` identity flags;
- a configuration-backed species registry;
- an initial `DOG` species entry;
- a `SpeciesCapabilityPack` representation;
- owner-scoped authorization;
- first-use canonical user provisioning;
- reusable request authentication dependencies;
- idempotent pet creation;
- deterministic local authentication for CI;
- one real Android → Firebase Auth → PETi API → Firestore development vertical slice.

Phase 1 does **not** implement AI, media, Cloud Credit consumption, rewarded advertising, Premium, Care, Timeline, measurements, veterinary records, specialist checks, or reports.

---

# 2. Phase 1 Architectural Result

The target runtime path is:

```text
Google Account
      ↓
Android Credential Manager
      ↓
Firebase Authentication
      ↓
Firebase ID token
      ↓
PETi Android API client
      ↓
Authorization: Bearer <Firebase ID token>
      ↓
PETi FastAPI
      ↓
Firebase token verification
      ↓
Canonical PETi User
      ↓
Authorization / ownership policy
      ↓
Firestore repositories
      ↓
User / Species / AnimalProfile data
```

Android must **not** access Firestore directly.

The canonical data path is:

```text
Android
   ↓ HTTPS
PETi API
   ↓
Firestore
```

not:

```text
Android
   ↓
Firestore
```

---

# 3. Phase 1 Hard Boundaries

Codex must preserve all Phase-0 architecture invariants and additionally enforce the following Phase-1 rules.

## P1-INV-001 — Firebase identity is not PETi authorization

A valid Firebase token proves authentication.

It does not by itself determine:

- PETi role;
- billing exemption;
- advertising exemption;
- pet ownership;
- future Cloud Credit balance;
- future Premium status.

Those properties are resolved from PETi backend state.

## P1-INV-002 — Client-supplied roles are never trusted

No public Android/API request may set:

```text
role
billing_exempt
ads_exempt
internal_persona
admin
```

These are trusted backend fields.

## P1-INV-003 — New users default to CUSTOMER

On first valid authenticated request:

```text
new PETi user
    ↓
role = CUSTOMER
billing_exempt = false
ads_exempt = false
```

unless a trusted server-side provisioning mechanism has explicitly created a different role.

## P1-INV-004 — ADMIN does not imply customer-data bypass

The ordinary customer endpoints remain owner-scoped even for an `ADMIN` user.

For example:

```text
GET /v1/pets/{pet_id}
```

may return only a pet owned by the authenticated PETi user.

Administrative support access to other users' data, if ever introduced, must use a separate reviewed operator surface.

## P1-INV-005 — Pet persistence is generic

Persistence uses:

```text
AnimalProfile
```

not:

```text
Dog
```

The user-facing product may initially expose only configured species, but persistence and service boundaries are species-generic.

## P1-INV-006 — Species are registry-controlled

The Android app must not decide:

```text
unknown species → DOG
```

The backend species registry determines whether a profile species is currently allowed.

## P1-INV-007 — Unsupported AI does not block profile creation architecture

Species profile support and AI support are separate concepts.

A species may eventually be:

```text
profile_enabled = true
AI capabilities = none
```

The data model must support that state.

## P1-INV-008 — No cross-account cache flash

When account identity is unresolved or changes, Android must never briefly render a pet cached for another user.

Selected-pet local state must be bound to the authenticated PETi user identity.

## P1-INV-009 — Firestore is backend-only

Customer Android code must not depend on Firestore client repositories.

Firestore access is performed by backend repositories using server credentials/IAM.

## P1-INV-010 — Pet creation is retry-safe

Repeated network submission using the same idempotency key must not create duplicate pets.

---

# 4. Phase 1 Work Packages

Implement Phase 1 as bounded Codex tasks. Do not give Codex the entire phase as one coding prompt.

Recommended sequence:

```text
P1-00  Phase-0 gate verification
P1-01  Identity dependencies and environment configuration
P1-02  Backend authentication abstractions
P1-03  Firebase token verification
P1-04  Canonical User domain and Firestore repository
P1-05  Authenticated principal / request dependency
P1-06  Trusted role and internal-user provisioning
P1-07  /v1/me bootstrap endpoint
P1-08  Species registry contracts
P1-09  Species Firestore/config repository
P1-10  Initial DOG registry seed
P1-11  AnimalProfile contracts
P1-12  AnimalProfile Firestore repository
P1-13  Generic idempotency mechanism
P1-14  Pet CRUD service
P1-15  Pet CRUD API
P1-16  Ownership and anti-enumeration hardening
P1-17  Android authentication domain boundary
P1-18  Android Credential Manager + Firebase implementation
P1-19  Authenticated API token provider
P1-20  Session restoration and sign-out
P1-21  Android species repository
P1-22  Android pet repository
P1-23  Pet creation UI
P1-24  Pet list / switcher UI
P1-25  Pet detail/edit/delete UI
P1-26  Selected-pet persistence
P1-27  Local deterministic auth path
P1-28  Backend integration tests
P1-29  Android emulator E2E
P1-30  Real DEV vertical slice
P1-31  Security and release-variant checks
P1-32  Observability
P1-33  Documentation and ADR closeout
P1-34  Phase exit gate
```

---

# 5. P1-00 — Verify the Phase-0 Gate

## Goal

Prove that Codex is building on the intended clean repository.

## Codex must

Run:

```bash
./scripts/check
```

and record the baseline result.

Also inspect:

```text
docs/ARCHITECTURE_INVARIANTS.md
docs/OBSOLETE_ARCHITECTURE.md
docs/SECRETS.md
docs/specs/
```

Verify:

- no local PETi AI dependency;
- no Android Gemini path;
- no global advertising manager;
- `LOCAL`, `DEV`, `STAGING`, `PRODUCTION` are defined;
- Android shell builds;
- backend shell starts.

## Do not

Do not "repair" Phase 0 by introducing unrelated feature code.

If Phase 0 is broken, repair only the broken Phase-0 contract first.

## Acceptance

```text
./scripts/check → 0
```

before P1-01 begins.

---

# 6. P1-01 — Add Identity Dependencies and Environment Configuration

## Goal

Prepare Android and backend for real Firebase authentication without implementing the UI yet.

## Android

Add the current stable, pinned dependencies required for:

- Android Credential Manager;
- Sign in with Google through Credential Manager;
- Firebase Authentication;
- Google services configuration required by Firebase.

Do not use the legacy Google Sign-In API as the primary implementation.

Keep all versions centralized in the existing dependency catalog/build logic.

## Backend

Add the current pinned dependencies required for:

- Firebase Admin authentication/token verification;
- Firestore server access.

Do not scatter initialization across route files.

## Environment configuration

Add typed settings such as:

```text
firebase_project_id
firestore_project_id
firestore_database_id
auth_mode
```

Possible `auth_mode` values:

```text
LOCAL_TEST
FIREBASE
```

Constraints:

```text
LOCAL environment       → LOCAL_TEST allowed
DEV/STAGING/PRODUCTION  → FIREBASE required
PRODUCTION              → LOCAL_TEST forbidden
```

The backend must fail startup if `LOCAL_TEST` is selected in production.

## Android environment behavior

Map:

```text
debug/local    → local test/fake auth permitted
internal/dev   → Firebase
internal/stage → Firebase
release/prod   → Firebase only
```

Release code must not silently fall back to fake authentication.

## Tests

Add tests proving:

- PRODUCTION rejects local auth mode;
- LOCAL accepts test auth mode;
- Firebase config is required where appropriate;
- release build does not wire fake auth as default.

## Do not

Do not implement:

- Play Billing;
- rewarded advertising;
- Gemini;
- Firestore Android SDK repositories.

---

# 7. P1-02 — Define Backend Authentication Abstractions

## Goal

Separate identity verification from PETi user/role resolution.

Create a backend contract such as:

```python
class ExternalIdentity:
    firebase_uid: str

class IdentityVerifier(Protocol):
    async def verify_bearer_token(self, token: str) -> ExternalIdentity:
        ...
```

Implementations:

```text
FirebaseIdentityVerifier
LocalTestIdentityVerifier
```

The verifier returns only external authenticated identity.

It does not return PETi role or entitlement.

## Error model

Map authentication failures to stable errors such as:

```text
AUTH_MISSING_TOKEN
AUTH_INVALID_TOKEN
AUTH_EXPIRED_TOKEN
AUTH_UNAVAILABLE
```

Use `401` for invalid/missing credentials.

Use a retryable service error only when identity infrastructure itself is unavailable and the distinction can be made safely.

## Logging

Log:

```text
authentication outcome category
correlation_id
```

Do not log:

```text
raw bearer token
Google ID token
Firebase ID token
email
credential contents
```

## Tests

- missing authorization header;
- unsupported auth scheme;
- empty bearer token;
- verifier success;
- verifier invalid;
- verifier expired;
- token never appears in logs.

---

# 8. P1-03 — Implement Firebase ID-Token Verification

## Goal

Implement the production `FirebaseIdentityVerifier`.

## Required behavior

Input:

```text
Authorization: Bearer <Firebase ID token>
```

Verify using the Firebase Admin SDK.

On success obtain:

```text
firebase_uid
```

Do not accept:

- raw Google OAuth access tokens;
- arbitrary Google account IDs;
- client-provided Firebase UID;
- unsigned test JWTs in cloud environments.

## Initialization

Firebase Admin initialization must use Application Default Credentials / runtime service identity in cloud environments.

Do not commit service-account JSON to the repository.

## Token lifetime

Treat expired/invalid tokens as authentication failures.

Do not persist ID tokens in the backend database.

## Tests

Unit tests should fake the Firebase verification adapter.

Create a focused integration test against the selected development/test Firebase configuration only where it can run safely.

## Do not

Do not put Firebase Admin initialization inside every request handler.

Use one application-scoped dependency/service.

---

# 9. P1-04 — Implement the Canonical PETi User Domain

## Goal

Create the first canonical PETi account record.

## Domain model

Implement:

```text
User
- id
- firebase_uid
- role
- billing_exempt
- ads_exempt
- internal_persona_code nullable
- created_at
- updated_at
- deleted_at nullable
```

Role enum:

```text
CUSTOMER
INTERNAL_TEST
ADMIN
```

## Privacy rule

Do not persist Google email, Google profile image, or Google display name merely because Firebase exposes them.

Only persist identity metadata required by the product.

If a future feature needs additional profile information, add it deliberately.

## Firestore storage

Recommended logical mapping:

```text
users/{firebase_uid}
```

Document content contains:

```text
id = internal opaque PETi user ID
firebase_uid = Firebase UID
...
```

This provides one deterministic Firestore document per Firebase identity while retaining a separate internal PETi user ID.

Use the PETi `id`, not the Firebase UID, as `owner_user_id` on product entities.

## First-use provisioning

Implement:

```text
get_or_create_user(firebase_uid)
```

Rules:

- if user exists and is active → return it;
- if user does not exist → atomically create CUSTOMER;
- if a deleted/disabled account state exists → fail according to account policy rather than silently creating a second account.

New automatic provisioning must always use:

```text
role = CUSTOMER
billing_exempt = false
ads_exempt = false
```

## Tests

- first call creates one user;
- second call returns same internal PETi `id`;
- concurrent provisioning does not create two users;
- client cannot influence role;
- user record contains no raw token.

---

# 10. P1-05 — Create the Authenticated PETi Principal

## Goal

Provide one reusable dependency for all authenticated API routes.

Create:

```text
AuthenticatedPrincipal
- firebase_uid
- user_id
- role
- billing_exempt
- ads_exempt
- internal_persona_code
```

Request resolution:

```text
Bearer token
   ↓
IdentityVerifier
   ↓
ExternalIdentity
   ↓
UserRepository.get_or_create_user
   ↓
AuthenticatedPrincipal
```

Expose a FastAPI dependency such as:

```text
require_authenticated_principal()
```

Future routes must use it rather than reimplement authentication.

## Important rule

The principal is created server-side.

Android cannot supply:

```text
user_id
role
billing_exempt
ads_exempt
```

as authority.

## Tests

- authenticated CUSTOMER;
- authenticated INTERNAL_TEST;
- authenticated ADMIN;
- no token;
- unknown user auto-provisions CUSTOMER;
- role in arbitrary request body/header has no effect.

---

# 11. P1-06 — Trusted Role and Internal-User Provisioning

## Goal

Provide a safe server-side mechanism to create/modify internal test users and the designated administrator.

## Create trusted script/tooling

Example:

```text
scripts/provision_user_role.py
```

Inputs should require explicit trusted values, for example:

```text
--firebase-uid
--role
--internal-persona-code
```

The tool may run only with trusted developer/operator credentials.

## Required behavior

### CUSTOMER

```text
billing_exempt = false
ads_exempt = false
```

### INTERNAL_TEST

```text
billing_exempt = true
ads_exempt = true
```

### ADMIN

```text
billing_exempt = true
ads_exempt = true
```

The phase only establishes these flags.

Actual Cloud Credit/Premium/advertising bypass rules are implemented in the funding phase.

## Security rule

There must be no customer endpoint such as:

```text
POST /v1/me/make-admin
PATCH /v1/me { role: ADMIN }
```

## Tests

- public API cannot modify role;
- CUSTOMER cannot self-elevate;
- provisioning script can create INTERNAL_TEST;
- provisioning script can create ADMIN;
- repeated provisioning is deterministic/auditable.

## Audit

Trusted role changes should emit a structured operator log:

```text
target PETi user id
old role
new role
operation
timestamp
```

Do not log credentials.

---

# 12. P1-07 — Implement `/v1/me`

## Goal

Create the first real authenticated PETi API endpoint.

Implement:

```text
GET /v1/me
```

Response example shape:

```text
id
role
billing_exempt
ads_exempt
internal_persona_code
created_at
```

Do not expose:

```text
firebase_uid
raw Firebase claims
tokens
backend credential information
```

unless there is a specific operational reason.

## Behavior

On the first valid authenticated request:

```text
Firebase identity
    ↓
PETi user auto-provision
    ↓
MeResponse
```

On later requests:

```text
same Firebase identity
    ↓
same PETi user
```

## Tests

- anonymous → 401;
- first login → user created;
- returning login → same PETi user ID;
- internal role returned correctly;
- no sensitive auth fields returned.

---

# 13. P1-08 — Define Species Registry Contracts

## Goal

Create species/profile capability contracts without implementing AI.

Define:

```text
SpeciesRegistryEntry
- species_code
- display_name
- profile_enabled
- public_enabled
- capability_pack_version nullable
```

Define or complete:

```text
SpeciesCapabilityPack
- species
- version
- profile_enabled
- supported_analysis_types
- enabled_analysis_types
- taxonomy_versions
- safety_policy_version nullable
- evaluation_certificate_ids
- public_enabled
```

Phase 1 must support:

```text
profile_enabled = true
enabled_analysis_types = []
```

This is important because profile support and AI release are independent.

## Contract behavior

Unknown species codes must not be coerced to `DOG`.

## API representation

Prepare:

```text
GET /v1/species
GET /v1/species/{species_code}/capabilities
```

## Tests

- known species serializes;
- unknown species is not defaulted;
- profile-only species state is valid;
- empty AI capabilities are valid.

---

# 14. P1-09 — Implement the Species Registry Repository

## Goal

Make species configuration backend-authoritative.

Create:

```text
SpeciesRegistryRepository
```

with operations such as:

```text
list_public_profile_species()
get_species(species_code)
get_capability_pack(species_code)
```

Production implementation may use Firestore configuration documents.

Local tests use an in-memory/fake implementation.

## Required rules

Pet creation requires:

```text
species exists
AND profile_enabled = true
AND public_enabled = true
```

AI capability state is irrelevant to profile creation.

## Do not

Do not hard-code:

```text
if species != DOG: reject
```

inside pet service code.

The registry owns that decision.

---

# 15. P1-10 — Seed the Initial DOG Registry Entry

## Goal

Provide the initial real species configuration without pretending Phase-1 AI exists.

Seed:

```text
species_code = DOG
profile_enabled = true
public_enabled = true
```

AI capability lists should reflect the implementation reality of Phase 1.

Do not mark unimplemented AI capabilities as customer-enabled.

Example conceptual state:

```text
supported_analysis_types = []
enabled_analysis_types = []
```

Later AI phases revise the species capability pack through explicit versioned changes.

## Important

The seed is implementation configuration, not Android hard-coding.

Android obtains available profile species from:

```text
GET /v1/species
```

---

# 16. P1-11 — Define `AnimalProfile` Contracts

## Goal

Create a generic pet profile sufficient for cloud CRUD and future expansion.

## Phase-1 canonical model

Implement at minimum:

```text
AnimalProfile
- id
- owner_user_id
- species
- display_name
- active_state
- avatar_media_id nullable
- created_at
- updated_at
- deleted_at nullable
```

Phase 1 should keep profile creation minimal:

```text
display_name
species
```

This matches the product rule that name + species are enough to create a pet.

## Future-compatible optional profile fields

The persistence model may reserve/introduce optional fields only when doing so does not create premature feature semantics.

Do not implement AI-derived profile truth in Phase 1.

In particular, do not implement:

```text
AI breed inference
AI age inference
AI sex inference
AI weight inference
```

## `active_state`

Use a representation that can support future states such as:

```text
ACTIVE
INACTIVE
```

Phase 1 may create pets as `ACTIVE`.

Commercial policy for inactive profiles belongs to later entitlement/funding work.

## Request DTOs

### Create

```text
CreateAnimalRequest
- display_name
- species
```

### Update

Allow only explicitly Phase-1 editable fields, for example:

```text
display_name
```

Species changes should be treated conservatively.

Recommended Phase-1 rule:

> Do not allow changing species through ordinary `PATCH` after creation.

If a user chose the wrong species, delete/recreate for Phase 1 or introduce a separate reviewed species-change operation later.

This avoids corrupting future species-specific history.

## Validation

- trim surrounding whitespace;
- reject empty display name;
- reject invalid/unavailable species;
- keep validation rules identical in backend contract and Android UI where practical;
- backend remains authoritative.

The current product specification does not define an exact maximum display-name length. If Codex introduces a technical maximum, it must be defined once in shared contract/configuration and documented as an implementation limit rather than silently duplicated.

---

# 17. P1-12 — Implement the Firestore `AnimalProfileRepository`

## Goal

Persist pets in Firestore behind a repository interface.

Create:

```text
AnimalProfileRepository
```

Operations:

```text
create
get_owned
list_owned
update_owned
soft_delete_owned
```

Recommended collection:

```text
animals/{animal_id}
```

Required stored ownership:

```text
owner_user_id = canonical PETi user id
```

Never use a client-supplied owner ID.

## Read behavior

All normal reads require authenticated owner context.

The repository/service must support an ownership-safe pattern such as:

```text
get animal_id
verify owner_user_id == principal.user_id
verify deleted_at is null
```

or query with owner constraint.

## List behavior

Return only:

```text
owner_user_id == authenticated user
deleted_at == null
```

## Delete behavior

Phase 1 should use a soft-delete/tombstone operation:

```text
deleted_at = server timestamp
```

and make the profile disappear from normal reads.

A later privacy/deletion phase performs full cascade/purge rules after dependent media, records, analyses, reminders and reports exist.

## Timestamps

Use server/backend time.

Do not trust Android timestamps for canonical `created_at` or `updated_at`.

## Tests

- create;
- retrieve;
- list;
- update;
- soft delete;
- deleted pet no longer listed;
- deleted pet returns not found;
- persistence survives repository/service restart;
- owner filter enforced.

---

# 18. P1-13 — Implement Generic Idempotency for Create Operations

## Goal

Prevent duplicate pet creation caused by retries/double taps/network uncertainty.

Implement a reusable server-side idempotency service.

Public create request requires:

```text
Idempotency-Key
```

Recommended record semantics:

```text
user_id
idempotency_key_hash
operation
request_fingerprint
result_resource_id
created_at
```

Do not store unnecessary raw request content if a hash/fingerprint is sufficient.

## Required behavior

### First request

```text
new key
    ↓
create pet
    ↓
store key/result atomically
    ↓
return pet
```

### Exact retry

```text
same user
same operation
same key
same request fingerprint
    ↓
return original pet/result
```

### Conflicting reuse

```text
same user
same operation
same key
different request
    ↓
409 IDEMPOTENCY_KEY_REUSE_CONFLICT
```

## Atomicity

Pet creation and idempotency registration must be atomic enough that a retry cannot create a second pet after a partial success.

Use the repository transaction abstraction.

## Tests

- first create;
- exact retry;
- concurrent duplicate calls;
- same key/different payload;
- same key used by different users remains isolated.

---

# 19. P1-14 — Implement `AnimalProfileService`

## Goal

Keep API routes thin and centralize business rules.

Create service methods such as:

```text
create_animal(principal, request, idempotency_key)
list_animals(principal)
get_animal(principal, animal_id)
update_animal(principal, animal_id, patch)
delete_animal(principal, animal_id)
```

## Create rules

1. principal is authenticated;
2. species registry entry exists;
3. profile species is enabled;
4. `owner_user_id` comes from principal;
5. name is validated;
6. idempotency is enforced;
7. profile starts `ACTIVE`;
8. no Cloud Credit is required.

## Important commercial rule

Creating an ordinary low-cost pet profile must not consume a Cloud Credit in Phase 1.

The funding system is for materially costly operations, not every small Firestore write.

## Update rules

- only owned pet;
- only allowed fields;
- no role/ownership fields in request;
- server owns timestamps.

## Delete rules

- only owned pet;
- soft delete;
- deleting already-deleted/non-owned pet returns safe not-found semantics.

---

# 20. P1-15 — Implement Pet CRUD API

## Goal

Expose the canonical pet API.

Implement:

```text
GET    /v1/pets
POST   /v1/pets
GET    /v1/pets/{pet_id}
PATCH  /v1/pets/{pet_id}
DELETE /v1/pets/{pet_id}
```

Implement:

```text
GET /v1/species
GET /v1/species/{species_code}/capabilities
```

## `GET /v1/pets`

Return only current user's non-deleted profiles.

## `POST /v1/pets`

Requires:

```text
Authorization
Idempotency-Key
CreateAnimalRequest
```

Response:

```text
201 Created
AnimalProfile
```

Exact idempotent replay may return the same representation with `200` or `201` according to the chosen contract, but the behavior must be stable and tested.

## `GET /v1/pets/{id}`

Return `200` only when owned.

Otherwise return `404`.

Do not distinguish:

```text
does not exist
exists but belongs to another user
```

to the caller.

## `PATCH`

Return updated owned profile.

Reject immutable fields.

## `DELETE`

Return `204` after successful soft deletion.

## Typed errors

At minimum:

```text
PET_NOT_FOUND
SPECIES_NOT_AVAILABLE
INVALID_PET_NAME
IDEMPOTENCY_KEY_REQUIRED
IDEMPOTENCY_KEY_REUSE_CONFLICT
```

All use the Phase-0 standard error envelope.

---

# 21. P1-16 — Ownership and Anti-Enumeration Hardening

## Goal

Treat authorization as a first-class feature.

Create tests using at least:

```text
User A
User B
Admin C
Internal D
```

## Mandatory behavior

User A cannot:

- GET User B's pet;
- PATCH User B's pet;
- DELETE User B's pet.

User B receives no indication that User A's pet exists.

ADMIN using ordinary customer routes also cannot read another customer's pet.

INTERNAL_TEST using ordinary customer routes also cannot read another customer's pet.

## Error semantics

For inaccessible resource IDs return a generic:

```text
404 PET_NOT_FOUND
```

rather than:

```text
403 THIS_PET_BELONGS_TO_SOMEONE_ELSE
```

## Logging

Backend internal logs may categorize authorization failures, but customer-facing responses must not leak ownership.

---

# 22. P1-17 — Create the Android Authentication Domain Boundary

## Goal

Prevent Credential Manager/Firebase APIs from leaking into every ViewModel.

Create a module/boundary such as:

```text
core:auth
```

if Phase-0 module policy permits adding it now.

Define:

```text
AuthRepository
```

State model:

```text
SignedOut
SigningIn
Authenticated
SessionRefreshing
AuthError
```

Expose:

```text
authState: Flow<AuthState>
signIn()
signOut()
getAccessToken(forceRefresh)
```

The rest of the app should not know Credential Manager implementation details.

## Test implementations

Provide:

```text
FakeAuthRepository
```

for deterministic UI/instrumentation tests.

---

# 23. P1-18 — Implement Credential Manager + Firebase Auth

## Goal

Build the real Android Google sign-in path.

## Flow

```text
User taps Continue with Google
        ↓
Credential Manager
        ↓
Google identity credential
        ↓
Firebase Authentication
        ↓
FirebaseUser
        ↓
Firebase ID token
        ↓
PETi API
```

## UI

Add minimal screens:

```text
Splash/session restore
Welcome
Continue with Google
Authentication error
```

Keep them clean and accessible.

Do not build the final entire onboarding experience yet.

## Required behavior

- explicit persistent `Continue with Google` action;
- credential-sheet cancellation is recoverable;
- no Google account available is recoverable;
- Firebase sign-in failure is recoverable;
- successful Firebase sign-in is not considered a complete PETi session until `/v1/me` succeeds;
- returning Firebase session proceeds to backend validation.

## Do not

Do not use:

```text
email/password PETi accounts
legacy Google Sign-In as primary auth
raw Google access token as PETi API bearer token
```

PETi API bearer token is the Firebase ID token.

---

# 24. P1-19 — Implement the Authenticated API Token Provider

## Goal

Ensure every authenticated API call has a valid Firebase ID token without storing raw tokens as application state.

Create:

```text
AccessTokenProvider
```

Production implementation resolves the token from the current Firebase user.

## API behavior

For authenticated requests:

```text
Authorization: Bearer <Firebase ID token>
```

## 401 recovery

Recommended bounded behavior:

```text
request
  ↓
401
  ↓
force-refresh Firebase ID token once
  ↓
retry same safe request once
  ↓
second 401
  ↓
session becomes invalid / require sign-in
```

Do not create infinite refresh loops.

For non-idempotent calls, retry only when the request has an idempotency key and request body can be safely replayed.

## Security

Do not persist bearer tokens in:

```text
SharedPreferences
DataStore
Room
logs
analytics
```

Firebase manages its own authentication persistence.

---

# 25. P1-20 — Session Restoration and Sign-Out

## Goal

Make reinstall/relaunch behavior trustworthy.

## App launch state machine

```text
STARTING
   ↓
Firebase user exists?
 ├─ no  → SIGNED_OUT
 └─ yes
      ↓
obtain token
      ↓
GET /v1/me
      ↓
canonical PETi user restored
      ↓
load pets
      ↓
select pet / create-first-pet route
```

## Important

Do not show protected cached pet content before the backend has resolved which PETi account is active.

## Sign-out

Sign out must:

1. clear PETi in-memory authenticated state;
2. clear selected-pet state tied to the session or leave it safely keyed by user;
3. sign out from Firebase;
4. clear Credential Manager state where required by the integration behavior;
5. return to Welcome.

Do not delete cloud PETi data.

## Account switch

When another Google account signs in:

- resolve a different canonical PETi user;
- never reuse the previous user's selected pet;
- never display previous user's pet cache.

## Tests

- returning Firebase user;
- expired backend session/token;
- sign out;
- sign in as another user;
- backend unavailable during restore;
- no pets;
- pets available.

---

# 26. P1-21 — Implement Android Species Repository

## Goal

Make pet species data-driven.

Define:

```text
SpeciesRepository
```

Production source:

```text
GET /v1/species
```

Expose a list/flow of species summaries.

## UI behavior

Pet creation must use the server-provided available species.

Do not use:

```kotlin
Species.DOG
```

as the only possible product-domain implementation.

A UI enum may exist for display concerns only if unknown registry values still fail safely and do not become DOG.

## Failure

If species cannot load:

- show retry;
- do not guess a species;
- do not create a pet with a hidden default.

---

# 27. P1-22 — Implement Android Pet Repository

## Goal

Create a clean Android data layer for cloud pet profiles.

Define:

```text
PetRepository
```

Operations:

```text
listPets()
createPet()
getPet()
updatePet()
deletePet()
```

Production implementation uses PETi API.

Fake implementation supports deterministic tests.

## Create

Generate a new idempotency key for a new logical creation attempt.

Preserve the same key across:

- transient network retry;
- token refresh retry;
- process-safe retry if supported.

Do not generate a new key merely because HTTP retry occurs.

## Error mapping

Map API errors to typed domain/UI errors:

```text
Unauthenticated
SpeciesUnavailable
InvalidName
Conflict
NetworkUnavailable
ServerUnavailable
Unknown
```

Do not expose raw server stack/debug information.

---

# 28. P1-23 — Implement Pet Creation UI

## Goal

Allow authenticated users with no pets to create the first profile manually.

## Screen

Create a focused `Create Pet` form.

Fields:

```text
Pet name
Species
```

Species comes from backend registry.

## States

```text
loading species
ready
submitting
success
validation error
species unavailable
network failure
server failure
```

## Behavior

- pet name required;
- species required;
- server remains authoritative;
- submit disabled while the same logical request is in flight;
- failed transient request can retry with the same idempotency key;
- success selects the new pet.

## No AI

Do not add:

```text
photo
breed inference
age inference
weight inference
initial scan
```

Those belong to later phases.

---

# 29. P1-24 — Implement Pet List / Switcher UI

## Goal

Provide the first multi-pet navigation primitive.

Display:

```text
pet display name
species display name
active state if relevant
```

Do not fabricate avatar imagery when no avatar exists.

Actions:

```text
select pet
add pet
open pet detail
```

The selected pet becomes Android presentation context only.

The server remains the source of pet ownership/existence.

## Empty state

Authenticated user with no pets:

```text
No pets yet
Add your first pet
```

## Multiple pets

Switching must update the selected-pet state deterministically.

Do not carry an unsaved mutation from one pet to another.

---

# 30. P1-25 — Implement Pet Detail, Edit and Delete UI

## Goal

Complete Phase-1 profile CRUD.

## Detail

Display at minimum:

```text
display name
species
```

## Edit

Phase 1 edits:

```text
display name
```

Do not add speculative profile facts not yet part of the implementation phase.

## Delete

Before delete:

- identify the exact pet;
- require explicit confirmation;
- explain that the pet profile will no longer appear.

Because Phase 1 has no analyses/media/records yet, do not invent downstream-deletion copy for nonexistent features.

Later phases expand this confirmation when dependent data exist.

## Delete behavior

After success:

- remove from local list;
- if deleted pet was selected, choose another owned pet;
- if no pet remains, route to create-pet state.

---

# 31. P1-26 — Selected-Pet Persistence

## Goal

Persist user convenience without turning local state into authority.

Store:

```text
canonical PETi user_id
selected_pet_id
```

using an appropriate small Android preference store.

## Launch resolution

After authenticated user and pet list load:

```text
saved user_id matches current user?
    ├─ no → ignore saved selected pet
    └─ yes
        ↓
saved pet still exists in returned owned list?
    ├─ yes → select it
    └─ no  → select deterministic fallback
```

Fallback:

```text
first available owned pet
```

or no selection if list empty.

## Security

Never show the selected pet before current account ownership is confirmed.

---

# 32. P1-27 — Deterministic Local Authentication Path

## Goal

Keep normal CI independent of real Google accounts while testing the same product boundaries.

Use the Phase-0 `IdentityVerifier` abstraction.

## Backend local mode

Implement:

```text
LocalTestIdentityVerifier
```

It accepts only a deliberately local/test credential format.

It must be impossible to enable in `DEV`, `STAGING`, or `PRODUCTION` unless a future explicit policy changes that boundary. Prefer `LOCAL` only.

## Android debug/instrumentation

Use:

```text
FakeAuthRepository
```

or a local test login adapter.

Test identities:

```text
test-user-a
test-user-b
test-internal
test-admin
```

These are deterministic test identities, not real Google accounts.

## Required parity

Local test authentication must still result in:

```text
ExternalIdentity
    ↓
canonical PETi user
    ↓
AuthenticatedPrincipal
```

Do not bypass ownership/service layers.

---

# 33. P1-28 — Backend Integration Test Suite

## Goal

Prove cloud-domain correctness before relying on UI tests.

Use local/emulated Firestore or an isolated disposable test datastore.

## Identity tests

- no token → 401;
- invalid token → 401;
- valid local test token → authenticated principal;
- first authenticated request creates CUSTOMER;
- returning request gets same PETi user;
- role spoof ignored.

## User tests

- internal provisioning;
- admin provisioning;
- billing/ads exemption flags;
- public API cannot update role.

## Species tests

- list public species;
- DOG available for profile creation;
- unknown species rejected;
- profile-enabled/AI-disabled state valid.

## Pet tests

- create;
- exact idempotent retry;
- idempotency conflict;
- list;
- get;
- rename;
- delete;
- deleted resource unavailable.

## Ownership tests

- A cannot get B;
- A cannot patch B;
- A cannot delete B;
- ADMIN ordinary route cannot access B;
- INTERNAL_TEST ordinary route cannot access B.

## Persistence tests

Restart backend/repository layer and verify data remains.

---

# 34. P1-29 — Android Emulator E2E Suite

## Goal

Prove the user journey without requiring real Google UI or paid services.

Use managed Android emulator/device infrastructure.

## E2E-01 — First-time user

```text
fresh install
→ local/fake sign-in User A
→ /v1/me provisions CUSTOMER
→ no pets
→ Create Pet
→ species registry loads
→ create DOG pet
→ pet selected
```

## E2E-02 — Relaunch

```text
kill app
→ relaunch
→ session restored
→ same PETi user
→ same cloud pet
→ selected pet restored
```

## E2E-03 — Multiple pets

```text
create second pet
→ switch pet
→ relaunch
→ selected pet remains
```

## E2E-04 — Account switch

```text
sign out User A
→ sign in User B
→ User A pets never visible
→ User B empty state
```

## E2E-05 — Delete selected pet

```text
two pets
→ select pet 2
→ delete pet 2
→ pet 1 becomes selected
```

## E2E-06 — Delete final pet

```text
one pet
→ delete
→ create-first-pet state
```

## E2E-07 — Species failure

```text
species service unavailable
→ create form does not guess DOG
→ retry available
```

## Accessibility

At minimum verify:

- sign-in button semantics;
- pet name field label;
- species selection semantics;
- delete confirmation;
- no state communicated only by color.

---

# 35. P1-30 — Real DEV Vertical Slice

## Goal

Prove the real Google identity/cloud persistence path at least once before closing Phase 1.

This is separate from deterministic CI.

## Required real path

```text
Android debug/internal build
        ↓
Credential Manager
        ↓
real Google account
        ↓
Firebase Authentication
        ↓
Firebase ID token
        ↓
DEV PETi API
        ↓
Firebase Admin token verification
        ↓
canonical PETi user
        ↓
DEV Firestore
        ↓
create/list/edit/delete pet
```

## Required evidence

Record:

- app build revision;
- backend build revision;
- environment = DEV;
- PETi user ID;
- created pet ID;
- API success;
- reinstall/re-auth persistence result.

Do not record raw ID tokens.

## Reinstall test

1. create pet in DEV;
2. uninstall app;
3. reinstall same build/configuration;
4. sign in with same Google account;
5. verify the same PETi user and pet data return.

This proves cloud authority.

---

# 36. P1-31 — Security and Release-Variant Hardening

## Goal

Close obvious identity/data-isolation holes before adding media or AI.

## Mandatory checks

### Android

- no Firebase service-account credential in APK;
- no backend service credential in APK;
- no raw test token bundled in release;
- fake-auth selector absent from release;
- no Firestore direct-client repository;
- no admin self-elevation UI.

### Backend

- no unauthenticated pet endpoint;
- no role field accepted from public DTOs;
- all pet operations owner-scoped;
- local auth forbidden in production;
- token values redacted;
- Firestore IAM/service account follows least privilege for the deployed API.

### Firestore

Because Android accesses PETi data through the backend, direct client access should be denied unless a future explicit architecture decision introduces it.

Do not rely on client-supplied Firestore document ownership.

## APK/AAB inspection

Add an automated or scripted inspection for:

```text
test-auth markers
service-account material
obvious secrets
forbidden debug endpoints
```

Phase 1 may inspect debug and release APKs; signed production AAB certification happens later.

---

# 37. P1-32 — Phase-1 Observability

## Goal

Introduce useful identity/profile telemetry without sensitive content.

## Backend operational events

Track:

```text
auth_verify_success
auth_verify_failure
user_created
user_restored
pet_created
pet_updated
pet_deleted
pet_listed
species_registry_read
authorization_not_found
```

Recommended safe dimensions:

```text
environment
role
operation
status
duration
correlation_id
```

Avoid general logging of:

```text
pet name
Firebase token
Google email
raw Firebase claims
```

## Android events

Minimal Phase-1 product events may include:

```text
sign_in_started
sign_in_completed
sign_in_failed
pet_create_started
pet_created
pet_selected
pet_updated
pet_deleted
sign_out_completed
```

Do not include the pet's name in analytics.

---

# 38. P1-33 — Documentation and ADR Closeout

## Goal

Make the implementation understandable to the next Codex task.

Update:

```text
README.md
docs/ARCHITECTURE_INVARIANTS.md
docs/specs/ implementation mapping if maintained
```

Create/complete ADRs:

```text
ADR-008 Firebase Authentication is external identity
ADR-009 PETi backend owns authorization
ADR-010 Android does not access Firestore directly
ADR-011 Generic AnimalProfile persistence
ADR-012 Species registry separates profile support from AI support
ADR-013 Customer pet endpoints remain owner-scoped for all roles
ADR-014 Pet creation uses idempotency keys
```

Document local test auth and why it cannot run in production.

Document the DEV authentication setup without committing credentials.

---

# 39. P1-34 — Phase 1 Exit Gate

Phase 1 is complete only when all of the following are true.

## Identity

- [ ] Android uses Credential Manager for Google sign-in.
- [ ] Firebase Authentication establishes Android identity.
- [ ] PETi API receives Firebase ID tokens.
- [ ] Backend verifies Firebase ID tokens.
- [ ] Invalid/expired tokens cannot access protected endpoints.
- [ ] First valid user becomes a canonical PETi `CUSTOMER`.
- [ ] Returning Firebase identity maps to the same PETi user.
- [ ] `CUSTOMER`, `INTERNAL_TEST`, and `ADMIN` exist.
- [ ] Role assignment is server-only.
- [ ] `billing_exempt` and `ads_exempt` exist.
- [ ] Internal/Admin exemption flags are server-authoritative.
- [ ] Customer cannot self-elevate.
- [ ] No email/password PETi account path exists.

## User isolation

- [ ] User A cannot read User B pet.
- [ ] User A cannot update User B pet.
- [ ] User A cannot delete User B pet.
- [ ] Ordinary ADMIN route does not bypass ownership.
- [ ] Ordinary INTERNAL_TEST route does not bypass ownership.
- [ ] Non-owned pet IDs return non-enumerating not-found behavior.

## Species

- [ ] Species registry is backend-authoritative.
- [ ] Android does not default unknown species to DOG.
- [ ] `SpeciesCapabilityPack` exists.
- [ ] Profile support and AI capability support are separate.
- [ ] Initial DOG profile registry entry exists.
- [ ] Phase-1 DOG AI capability list does not falsely enable unimplemented AI.

## AnimalProfile

- [ ] Persistence uses `AnimalProfile`, not `Dog`.
- [ ] Pet requires only name + species to create.
- [ ] `owner_user_id` is assigned server-side.
- [ ] Pet list returns only authenticated user's pets.
- [ ] Pet detail works.
- [ ] Pet rename works.
- [ ] Pet deletion works.
- [ ] Delete is represented safely for future cascade handling.
- [ ] Create is idempotent.
- [ ] Duplicate network retry does not create duplicate pet.
- [ ] Same idempotency key with conflicting payload is rejected.

## Android

- [ ] Sign-in UI works.
- [ ] Authentication failures are recoverable.
- [ ] Session restoration works.
- [ ] Pet creation UI works.
- [ ] Species loads from backend.
- [ ] Pet list/switcher works.
- [ ] Pet detail/edit/delete works.
- [ ] Selected pet survives normal relaunch.
- [ ] Selected pet is scoped to current PETi user.
- [ ] Account switch never exposes previous account pet data.
- [ ] Sign-out works.
- [ ] Release build has no fake-auth UI.

## Persistence

- [ ] Firestore is the canonical profile store.
- [ ] Android does not use Firestore as a direct canonical client repository.
- [ ] Pet survives backend restart.
- [ ] Pet survives Android process death.
- [ ] Pet survives Android reinstall when same Google account signs back in.

## Testing

- [ ] Backend unit tests pass.
- [ ] Backend integration tests pass.
- [ ] Cross-user authorization suite passes.
- [ ] Idempotency tests pass.
- [ ] Android unit tests pass.
- [ ] Android emulator E2E passes.
- [ ] Account-switch E2E passes.
- [ ] DEV real Google/Firebase vertical slice has been executed successfully.

## Security

- [ ] No Firebase service-account key is committed.
- [ ] No Firebase ID token is logged.
- [ ] No role is accepted from public request bodies.
- [ ] LOCAL test auth cannot run in production.
- [ ] Firestore is protected from unintended direct client access.
- [ ] Release artifact contains no test-auth credential.
- [ ] Secret scan passes.

## Quality

- [ ] `ruff` passes.
- [ ] `mypy` passes.
- [ ] Android lint passes.
- [ ] Android unit tests pass.
- [ ] Architecture checks pass.
- [ ] `./scripts/check` returns `0`.

---

# 40. Required Phase-1 Test Matrix

Codex should not consider the phase complete without at least this matrix.

| Case | Expected result |
|---|---|
| No bearer token | 401 |
| Invalid Firebase token | 401 |
| First valid Firebase user | CUSTOMER created |
| Same Firebase user again | Same PETi user |
| Client sends fake role | Ignored/rejected |
| CUSTOMER tries admin elevation | Impossible |
| DOG registry lookup | Profile-enabled |
| Unknown species create | Rejected |
| Create pet | Success |
| Retry same create/idempotency key | Same pet |
| Same key/different request | 409 conflict |
| User A lists pets | Only A |
| User B lists pets | Only B |
| A requests B pet ID | 404 |
| A patches B pet | 404 |
| A deletes B pet | 404 |
| ADMIN requests B pet through customer endpoint | 404 |
| Rename own pet | Success |
| Delete own pet | Success |
| Get deleted pet | 404 |
| Selected pet relaunch | Restored |
| Selected pet deleted | Safe fallback |
| Sign out A → sign in B | No A data shown |
| Species service unavailable | No hidden DOG default |
| App reinstall + same account | Cloud pets restored |
| Release build inspection | No test auth / secrets |

---

# 41. Suggested Firestore Logical Structure After Phase 1

```text
users/
  {firebase_uid}
    id
    firebase_uid
    role
    billing_exempt
    ads_exempt
    internal_persona_code
    created_at
    updated_at
    deleted_at

species_registry/
  DOG
    species_code
    display_name
    profile_enabled
    public_enabled
    capability_pack_version

species_capability_packs/
  DOG
    species
    version
    profile_enabled
    supported_analysis_types
    enabled_analysis_types
    taxonomy_versions
    safety_policy_version
    evaluation_certificate_ids
    public_enabled

animals/
  {animal_id}
    id
    owner_user_id
    species
    display_name
    active_state
    avatar_media_id
    created_at
    updated_at
    deleted_at

idempotency/
  {opaque_hash}
    user_id
    operation
    request_fingerprint
    result_resource_id
    created_at
```

Exact collection naming may differ, but the ownership and authority semantics must not.

---

# 42. Suggested Android Module Shape After Phase 1

```text
android/
├── app/
├── core/
│   ├── common/
│   ├── model/
│   ├── network/
│   ├── auth/
│   ├── ui/
│   └── testing/
└── features/
    ├── auth/
    └── pets/
```

If the project prefers flatter naming, `feature-auth` and `feature-pets` are also acceptable.

The important rule is dependency direction, not directory aesthetics.

Recommended dependency direction:

```text
feature-auth
    ↓
core-auth
    ↓
core-network/common

feature-pets
    ↓
core-network/model/ui
```

`feature-pets` must not depend directly on Firebase Authentication implementation classes.

---

# 43. Suggested Backend Dependency Direction

```text
API routes
    ↓
Services
    ↓
Domain contracts
    ↓
Repository interfaces

Infrastructure adapters
    ├── Firebase identity verifier
    └── Firestore repositories
```

Avoid:

```text
route
  ↓
Firestore SDK directly
```

and:

```text
domain service
  ↓
Firebase Admin global singleton
```

---

# 44. Codex Task Prompt Template for Phase 1

Every Phase-1 subtask given to Codex should use this pattern:

```text
TASK
Implement <P1 task name>.

SOURCE OF TRUTH
- PETi Functional Product Specification v1.0.0-cloud
- PETi Technical Specification v1.0.0-cloud
- PETi Cloud Architecture Specification v1.0.0-cloud
- PETi Phase 0 architecture invariants
- This Phase 1 build plan

PRECONDITION
./scripts/check must be green before changes.

SCOPE
List exact modules/directories Codex may modify.

REQUIRED BEHAVIOR
List the task-specific behavior from this document.

SECURITY INVARIANTS
- Never trust client role.
- Never trust client ownership.
- Never log bearer tokens.
- Do not add direct Android Firestore access.
- Do not add AI/media/billing/ads.

FAILURE BEHAVIOR
List typed API/UI failures required for the task.

TESTS
Specify the new unit/integration/emulator tests.

DO NOT
List explicit non-goals.

VALIDATION
Run focused tests first.
Then run:
./scripts/check

COMPLETION REPORT
Return:
- files changed;
- behavior implemented;
- tests added;
- exact commands executed;
- pass/fail results;
- any remaining limitation.
```

---

# 45. Recommended Codex Task Sizing

A single Codex task should normally implement one of:

```text
one backend contract + tests
one repository + tests
one service rule + tests
one API group + integration tests
one Android repository + tests
one Android screen/state flow + tests
one emulator E2E flow
```

Do not ask one Codex run to implement:

```text
all Firebase auth + all pet CRUD + all Android UI + all tests
```

The phase should be built through bounded evidence-producing increments.

---

# 46. What Codex Must NOT Implement in Phase 1

Explicitly out of scope:

```text
Gemini provider
AI analysis jobs
Cloud Tasks
media upload
CameraX
Photo Picker
audio capture
Initial Scan
PETi Check
Dental Check
Feces Check
Body Check
AI profile suggestions
AI breed inference
AI age inference
AI sex inference
AI weight inference
Cloud Credit balance rules
Cloud Credit rewarded grants
rewarded ads
advertising SDK
Premium
Google Play Billing
Timeline
Care/reminders
measurements
temperature
veterinary documents
weekly reports
FCM notifications
account deletion cascade
production AI deployment
```

Do not add speculative stubs for all of them unless a tiny interface is already required by Phase-0 architecture.

---

# 47. Phase 1 Definition of Done

Phase 1 is **DONE** when PETi has a real, secure cloud identity and pet-domain backbone.

The key proof is:

```text
real Android
    ↓
Google Credential Manager
    ↓
Firebase Auth
    ↓
Firebase ID token
    ↓
PETi Cloud API
    ↓
canonical PETi user
    ↓
server ownership checks
    ↓
Firestore AnimalProfile
    ↓
Android pet list/selection
```

combined with deterministic local CI proving:

```text
authentication boundaries
role boundaries
species boundaries
ownership boundaries
idempotency
session restoration
account switching
pet CRUD
```

with no AI, advertising, billing, or media complexity mixed into the phase.

Only after this gate passes should implementation move to:

# Phase 2 — Cloud Credits, Cost Classes and Funding Resolution

Phase 2 will build the server-authoritative economic layer that determines how materially costly cloud operations are funded, while ordinary pet/profile use remains clean and ad-free.
