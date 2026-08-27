# PETi — Functional Product Specification

**Version:** 1.0.0-cloud  
**Date:** 2026-08-12  
**Status:** Canonical product baseline  
**Primary client:** Native Android  
**Product scope:** Companion animals / pets  
**Initial certified AI species:** Dog  
**AI runtime:** Cloud-only  
**Commercial model:** Free-first with opt-in rewarded funding for variable-cost cloud operations; optional Premium

# 1. Product definition

PETi is an AI-assisted care, observation, organization and longitudinal-history application for companion animals.

The product is intended to support **any pet species at the profile and care-management level**, while AI capabilities are enabled only for species and tasks that have passed their own evaluation and safety gates.

The first fully supported AI species is:

`DOG`

The product architecture must allow future independently certified capability packs such as:

- `CAT`;
- `RABBIT`;
- `BIRD`;
- `HORSE`;
- other companion animals.

PETi must never silently apply dog-specific interpretation, taxonomy, reference information or safety rules to another species.

---

# 2. Product mission

> Help pet owners collect better information, understand observable changes, organize care and know when professional veterinary attention may be appropriate—without pretending that an AI application can replace veterinary examination or diagnosis.

PETi should be:

- honest;
- genuinely useful;
- easy to use;
- accessible;
- cloud-powered;
- evidence-aware;
- longitudinal;
- cost-conscious;
- transparent about uncertainty;
- transparent about how cloud operations are funded.

---

# 3. Core product principles

## FP-01 — Useful without payment

PETi Free must be a real application, not a crippled trial.

Ordinary pet-management functionality must remain usable without subscription and without advertising interruptions.

This includes, subject only to reasonable abuse and storage limits:

- pet profile management;
- pet switching;
- Timeline browsing;
- Care;
- reminders;
- measurement entry;
- veterinary-record organization;
- viewing previously generated results;
- account settings;
- privacy controls;
- deletion controls.

## FP-02 — No ambient advertising

PETi SHALL NOT show:

- banner advertising;
- feed advertising;
- random interstitial advertising;
- automatic ads during navigation;
- ads inserted into Home;
- ads inserted into Timeline;
- ads inserted into Care;
- ads inserted into existing analysis results;
- ads inserted into veterinary records;
- ads inserted into safety guidance.

PETi should normally feel like an **ad-free application**.

## FP-03 — Advertising funds cost-bearing operations

Advertising may be offered only when:

1. the user explicitly requests an operation;
2. that operation creates a material variable cloud cost;
3. available free, sponsored, Premium or other credits are insufficient;
4. PETi clearly explains the available funding options;
5. the user voluntarily chooses the rewarded-ad option.

Typical variable-cost operations include:

- Gemini AI analysis;
- cloud media preprocessing;
- AI document extraction;
- retained cloud media beyond the included allowance;
- future compute-intensive cloud services.

## FP-04 — Explicit rewarded-ad consent

Advertising must never surprise the user.

The flow is:

`request operation → determine funding → offer rewarded ad → user explicitly accepts → ad → server verifies reward → credit → operation`

Not:

`request operation → unexpected advertisement`

## FP-05 — One funded operation means one complete result

PETi SHALL NOT require another advertisement to reveal:

- analysis details;
- red flags;
- urgency;
- safety guidance;
- limitations;
- recommended actions;
- provenance.

Once an operation has been funded and accepted, its complete customer result is available.

## FP-06 — No advertising influence over PETi output

Advertisers and sponsors SHALL NOT influence:

- observations;
- interpretation;
- urgency;
- confidence;
- safety classification;
- evidence selection;
- professional-care guidance;
- AI prompt content;
- model selection for clinical benefit;
- guardrail behavior.

The AI/safety pipeline finishes independently from advertising selection.

## FP-07 — Cloud-only AI

All AI inference and meaningful AI preprocessing occur through PETi-controlled cloud services.

PETi SHALL NOT ship:

- customer inference models;
- LiteRT AI pipelines;
- local VLM/LLM inference;
- a local model registry;
- downloadable specialist models;
- offline AI fallback.

Offline mode may expose cached read-only information, but it does not execute AI analysis.

## FP-08 — Evidence before certainty

Every AI workflow distinguishes:

- observed evidence;
- owner-reported context;
- measured information;
- documented information;
- estimates;
- possible interpretations;
- uncertainty;
- safety guidance.

## FP-09 — Quality before breadth

Implemented does not mean released.

Every AI capability requires:

- explicit functional contract;
- output schema;
- semantic guardrails;
- automated tests;
- held-out evaluation;
- safety evaluation;
- feature flag;
- release approval.

---

# 4. Identity and accounts

## FR-AUTH-001 — Google sign-in

PETi uses Google sign-in on Android.

A returning user must recover the same cloud account and data.

Authentication state is validated server-side.

## FR-AUTH-002 — Roles

Roles are:

- `CUSTOMER`;
- `INTERNAL_TEST`;
- `ADMIN`.

Roles are authorization properties and are independent of commercial funding state.

## FR-AUTH-003 — Administrator

The designated administrator account is:

- billing exempt;
- advertising exempt;
- product-quota exempt;
- allowed unlimited pets from the product perspective;
- allowed unlimited AI/cloud credits from the product perspective;
- permitted to access internal testing functionality.

Infrastructure safety limits still apply.

## FR-AUTH-004 — Internal personas

PETi retains server-created testing personas representing bounded commercial configurations.

Internal users:

- never need to watch real advertisements;
- use test/fake advertising;
- are billing exempt;
- can use fixture media;
- cannot self-elevate from the Android client.

---

# 5. Pet profiles and species

## FR-PET-001 — Generic pet entity

The canonical domain object is `AnimalProfile`, not `Dog`.

Minimum fields:

- `id`;
- `owner_user_id`;
- `species`;
- `display_name`;
- avatar;
- date of birth or approximate life stage;
- sex when owner-supplied;
- neuter/spay/reproductive status where relevant and owner-supplied;
- breed/type where relevant;
- measured weight;
- optional notes;
- timestamps;
- provenance for derived/confirmed facts.

## FR-PET-002 — Species registry

Species are configuration-backed.

Each species has:

- profile schema;
- display terminology;
- enabled care categories;
- measurement rules;
- enabled AI capabilities;
- safety rules;
- evaluation/certification status.

## FR-PET-003 — Unsupported AI species

A user may manage a pet whose AI capability pack is unavailable.

PETi must state:

> “AI analysis for this species is not available yet.”

It must never default to `DOG`.

## FR-PET-004 — Multiple pets

Users may maintain multiple pet profiles.

Exact commercial limits, if any, are server-configured.

Creating an additional low-cost profile should not be artificially tied to AI consumption unless required by measured product economics.

---

# 6. Onboarding

## FR-ONBOARD-001 — Fast manual onboarding

Minimum viable pet creation requires:

- name;
- species.

Everything else may be added later.

## FR-ONBOARD-002 — Optional AI onboarding

For a certified species, PETi may offer an optional AI-assisted Initial Scan.

For dogs, this may use a guided approximately 20-second capture.

The user can skip it.

## FR-ONBOARD-003 — No fabricated profile truth

AI suggestions do not automatically become authoritative.

User-confirmed facts and measured/documented information remain distinct from AI suggestions.

## FR-ONBOARD-004 — Cost funding

If Initial Scan AI incurs a cloud cost:

- use included allowance where available;
- otherwise offer an explicit rewarded funding flow;
- alternatively offer Premium/sponsor credit where applicable.

The user must always retain manual onboarding without watching an ad.

---

# 7. Cloud Credit system

## FR-CREDIT-001 — Server-authoritative Cloud Credits

PETi uses an internal server-authoritative credit ledger for variable-cost operations.

Possible funding sources:

- `FREE_ALLOWANCE`;
- `REWARDED_AD`;
- `SPONSOR`;
- `PREMIUM`;
- `PROMOTIONAL`;
- `INTERNAL_TEST`;
- `ADMIN_EXEMPT`.

Credits are not cryptocurrency, cash or transferable value.

They are internal service entitlements.

## FR-CREDIT-002 — Cost classes

Operations may belong to different cost classes.

Examples:

- `AI_PHOTO_STANDARD`;
- `AI_AUDIO`;
- `AI_VIDEO`;
- `AI_DOCUMENT_EXTRACTION`;
- `AI_SPECIALIST`;
- `MEDIA_RETENTION`;
- future configured classes.

Exact credit prices are server-side configuration derived from measured economics.

## FR-CREDIT-003 — Credit bundles

One rewarded advertisement may grant more than one reusable Cloud Credit.

PETi must not enforce one-advertisement-per-action when measured economics allow a better experience.

## FR-CREDIT-004 — Funding priority

A request may resolve funding in approximately this order:

1. admin/internal exemption;
2. Premium allowance;
3. included free allowance;
4. existing rewarded/sponsor/promotional credits;
5. offer additional rewarded funding;
6. decline/postpone operation.

No Android client decision is authoritative.

## FR-CREDIT-005 — No double charging

Retries, duplicate callbacks, queue redelivery or process restoration must not consume the same logical credit twice.

---

# 8. Rewarded advertising

## FR-ADS-001 — Rewarded only

Customer advertising in the initial product is opt-in rewarded advertising.

No ordinary advertising inventory is required.

## FR-ADS-002 — Clear value exchange

Before the ad, PETi states the benefit.

Examples:

> “Watch a short ad to get 3 PETi Cloud Credits.”

or:

> “This AI analysis requires one Cloud Credit. Watch an ad to continue for free.”

## FR-ADS-003 — Server verification

Credits are granted only after trusted server verification of the rewarded event.

The Android client cannot grant itself credits.

## FR-ADS-004 — Canceled advertisement

If the user cancels or does not satisfy the reward condition:

- no credit is granted;
- no cloud operation is started;
- no existing data is lost.

## FR-ADS-005 — Advertising unavailable

If no rewarded inventory is available:

PETi must not fabricate successful funding.

Possible alternatives:

- use existing credits;
- wait and retry;
- use Premium;
- use a sponsored credit if available;
- perform a cheaper/no-retention variant where technically appropriate.

## FR-ADS-006 — Safety contexts

PETi never interrupts an existing safety-critical result with advertising.

No ad is required to view professional-contact or urgent-care guidance.

---

# 9. Cloud media

## FR-MEDIA-001 — Capture and selection

Android supports:

- CameraX image capture;
- CameraX video capture;
- audio capture;
- Android Photo Picker;
- Android document picker/SAF.

## FR-MEDIA-002 — Cloud upload

Media required for AI analysis is uploaded to private cloud storage through authorized upload sessions.

## FR-MEDIA-003 — Ownership

Every media object is associated with an authenticated owner and optional animal.

Cross-account access is forbidden.

## FR-MEDIA-004 — Retention choices

PETi distinguishes:

- transient source media;
- retained user media;
- profile media;
- veterinary documents;
- derived structured results.

Source media need not be retained indefinitely for the result to remain useful.

## FR-MEDIA-005 — Storage funding

A base cloud-storage allowance may be included free.

When additional retained storage has material variable cost, PETi may offer Cloud Credits.

The user should be offered privacy/cost-conscious alternatives where practical, such as:

> “Analyze this media and delete the source after the retention period.”

versus:

> “Keep the original in PETi.”

## FR-MEDIA-006 — No ad for ordinary metadata

Creating pet records, text notes or small structured Timeline data does not individually trigger advertisements merely because the data are stored in Firestore.

Advertising is reserved for **material** variable cloud cost.

---

# 10. PETi Check

## FR-CHECK-001 — Generic analysis

A certified species/capability can submit supported:

- photo;
- video;
- audio;
- user question;
- immediate context.

## FR-CHECK-002 — Structured result

A result contains:

- summary;
- observable findings;
- uncertainty;
- possible interpretations;
- alternative explanations where material;
- confidence/evidence quality;
- urgency/safety state;
- recommended next observations/actions;
- red flags;
- limitations;
- provenance.

## FR-CHECK-003 — Observation vs interpretation

PETi must never collapse observation and interpretation into one undifferentiated narrative.

## FR-CHECK-004 — Abstention

`INSUFFICIENT_EVIDENCE` is a valid successful outcome.

PETi must prefer abstention to fabricated certainty.

## FR-CHECK-005 — Cost transparency

Before submission PETi knows whether:

- the operation is covered;
- credits are required;
- the user must fund the operation.

A technically rejected preflight must not consume a successfully reserved AI credit when expensive analysis was never accepted.

---

# 11. Dog AI capability pack

The initial `DOG` capability pack may contain independently released:

- Initial Scan;
- general visual Check;
- behavior video;
- audio;
- Feces Check;
- Dental Check;
- Body Check;
- document extraction;
- longitudinal comparisons.

Each remains independently feature-gated.

---

# 12. Dental Check

Dental Check remains visible-observation-only.

Required concepts include:

- front/left/right guided capture;
- optional additional view;
- no forced mouth opening;
- capture-quality state;
- visible calculus;
- gingival redness;
- visible swelling;
- visible bleeding;
- suspected visible recession;
- suspected tooth damage;
- discoloration;
- suspected missing tooth;
- lesion/mass/ulcer-like visible area;
- uncertainty;
- longitudinal comparison when comparable.

PETi must not claim from ordinary photographs:

- periodontal stage;
- pocket depth;
- root health;
- bone status;
- pulp vitality;
- definitive abscess;
- absence of hidden disease.

---

# 13. Feces Check

Feces Check may describe visible:

- consistency;
- general appearance;
- mucus-like material;
- fresh-red blood-like material;
- black/tarry appearance;
- foreign-material-like content;
- worm/segment-like structures without organism identification.

It must not claim from a photograph:

- parasite-free status;
- named parasite infection;
- bacterial/viral infection;
- occult blood;
- microbiome status;
- internal-organ diagnosis;
- definitive cause of diarrhea/constipation.

---

# 14. Veterinary Record Vault

Users can store private veterinary records.

Supported workflows include:

- upload;
- private source storage;
- document classification;
- AI extraction where funded/enabled;
- candidate-fact review;
- Confirm;
- Correct;
- Reject;
- source-page traceability.

AI extraction output remains a proposal until owner review where material.

Original source values and units are preserved.

---

# 15. Measurements

PETi supports at minimum:

- weight;
- temperature.

Source classes remain visibly distinct:

- `MEASURED`;
- `DOCUMENTED`;
- `OWNER_REPORTED`;
- `AI_ESTIMATED`.

Original units are preserved.

Conflicting measurements may coexist.

PETi must not claim that an ordinary smartphone measures core body temperature.

---

# 16. Care and reminders

Care includes:

- vaccinations;
- parasite prevention;
- appointments;
- medication/follow-up schedule;
- Body Check;
- custom events.

PETi does not generate medication dosage.

Reminder data remain available independently of notification permission.

---

# 17. Timeline and longitudinal intelligence

Timeline is the canonical user-facing history.

It preserves provenance across:

- AI observations;
- measurements;
- confirmed records;
- Care events;
- reminders;
- Body Checks;
- reports.

Longitudinal comparison requires:

- same animal;
- compatible species capability;
- comparable modality;
- compatible taxonomy/version;
- sufficient evidence.

PETi distinguishes:

- meaningful change;
- no meaningful change;
- insufficient comparable evidence.

---

# 18. Weekly PETi Report

Reports may summarize:

- observations;
- changes;
- stability;
- insufficient evidence;
- Care;
- measurements;
- records;
- Body Check;
- next useful observation.

Every material claim should be traceable to source records.

Report generation that uses Gemini is a variable-cost cloud operation and may consume configured Cloud Credits.

A deterministic/no-AI summary may be provided where appropriate without additional AI cost.

---

# 19. Safety

PETi remains non-diagnostic.

Safety routing is controlled by deterministic policy independent of free-form model wording.

Safety states may include:

- normal information;
- monitor;
- professional review recommended;
- prompt veterinary contact;
- urgent veterinary contact;
- safety blocked.

PETi never:

- diagnoses definitively from ordinary media;
- gives medication doses;
- fabricates measurements;
- suppresses a red flag because the user asked it to;
- allows advertising to downgrade safety.

---

# 20. Privacy

Pet media may contain human voices, homes, faces, documents and identifying context and must therefore be treated as private user content.

Requirements include:

- minimal Android permissions;
- private cloud storage;
- short-lived scoped access URLs;
- explicit retention policy;
- account deletion;
- media deletion;
- research consent separate from product use;
- no raw content in ordinary analytics;
- no secrets or tokens in logs.

---

# 21. Premium

Premium is optional.

Its role is convenience and higher resource availability, not making the basic product useful.

Possible Premium benefits:

- larger Cloud Credit allowance;
- no need to watch rewarded ads under ordinary usage;
- increased retained-media allowance;
- higher analysis limits;
- household/pet conveniences;
- advanced certified features.

Exact pricing and allowance are configuration/business decisions, not hard-coded functional requirements.

---

# 22. Explicit non-goals

PETi does not include in the initial release:

- iOS consumer application;
- consumer web application;
- social network;
- marketplace;
- automatic emergency calling;
- tele-veterinary diagnosis;
- prescription generation;
- medication-dose generation;
- definitive diagnosis/prognosis;
- genetic ancestry inference from appearance;
- exact age inference from imagery;
- neuter/spay inference from imagery;
- uncalibrated precise weight claims;
- smartphone core-temperature measurement;
- customer-facing local AI models;
- LiteRT inference;
- offline AI analysis;
- local model downloads or model management.

---

# 23. Functional Definition of Done

A capability is complete only when:

- functional acceptance criteria exist;
- Android states exist;
- server behavior exists;
- permissions are minimal;
- cost/funding behavior is defined;
- retries are idempotent;
- privacy behavior is defined;
- source/provenance semantics are preserved;
- deterministic tests pass;
- AI evaluation passes where applicable;
- safety evaluation passes where applicable;
- unsupported states fail closed;
- telemetry exists;
- the feature can be disabled server-side.