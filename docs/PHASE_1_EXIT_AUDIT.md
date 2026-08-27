# Phase 1 implementation audit

Implemented and locally verified:

- deterministic local bearer authentication and authenticated principal resolution;
- canonical PETi users with server-authoritative role and exemption flags;
- generic backend `AnimalProfile` model and owner-scoped CRUD;
- backend-authoritative species capability registry with a versioned DOG capability pack and profile-only CAT pack; AI release enablement remains governed by specialist flags/certificates and external certification evidence;
- soft deletion and idempotency-key protected creation;
- Android auth, token, species, pet, and selected-pet boundaries with fake implementations;
- shared `PetViewModel`, persistent user-scoped selected-pet storage, pet creation/list/edit/delete controls, and managed-emulator Compose coverage;
- Firebase/Firestore adapter selection when `PETI_AUTH_MODE=FIREBASE`, with deterministic credential-free LOCAL mode;
- Floci GCP emulator integration for local Firestore persistence, including owner isolation, idempotent create, update, and soft delete;
- Phase 1 backend and Android unit coverage.

The real DEV vertical slice requires project-specific Firebase configuration and operator credentials, which are not committed to this repository. It remains intentionally deferred by project policy; the local equivalent is reproducibly verified with `scripts\test-floci.ps1` and requires no cloud account.
