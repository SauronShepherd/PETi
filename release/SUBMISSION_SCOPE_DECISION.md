# PETi submission scope decision

Status: `SOURCE_DECISION_RECORDED_EXTERNAL_SUBMISSION_PENDING`
Decision date: 2026-08-27

## Decision

This release candidate is scoped for the hackathon submission and demo only.
It is not a declaration of Google Play production readiness. The submitted
product configuration keeps Premium/Google Play Billing out of scope and the
release is treated as a free product for this submission.

## Included scope

- Repository implementation and local quality gates.
- Bounded non-production GCP/Gemini evidence that is explicitly labeled as
  sandbox evidence.
- The agentic PETi workflow and safety/privacy design described in the
  Devpost draft, subject to the evidence limitations recorded in
  `release/EXTERNAL_GATES.md`.

## Excluded scope

- Google Play production launch, Play Console submission, and license-tester
  billing lifecycle certification.
- Production Firebase/GCP deployment and production signing.
- Claims of physical-device certification, legal approval, or complete
  provider/specialist certification.

## Release-language rule

Devpost and demo materials must distinguish implemented source behavior,
bounded sandbox evidence, and pending external certification. No `PENDING`
certificate or external gate may be promoted based only on local tests or
sandbox liveness.

If the product scope later changes to enable Premium or a Play production
launch, this decision is superseded by a separately reviewed production scope
record and the complete Play/production checklist becomes mandatory.
