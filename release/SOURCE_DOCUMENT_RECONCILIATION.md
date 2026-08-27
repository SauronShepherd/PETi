# PETi source-document reconciliation

Status: `SOURCE_RECONCILIATION_COMPLETE_EXTERNAL_REFERENCE_SET_UNAVAILABLE`
Date: 2026-08-27

## Scope

The repository was audited against the external document paths named in the
project request. Those files are not present in the current workspace and
could not be independently read or hashed. This record therefore reconciles
the authoritative documents available in this repository and explicitly lists
the unresolved external-reference limitation.

## Architecture clarification

The repository implementation uses the official `google-genai` SDK for the
Gemini provider (`backend/app/ai/providers/`) and a PETi-owned bounded
state-machine orchestrator (`backend/app/agent_runtime/`). There is no
`google.adk` import in the source tree. Any external HLD/LLD wording that
describes Google ADK must therefore be treated as a proposed/external design,
not as a claim about the current implementation.

For submission language, describe the implementation as “Google Gemini via
the official GenAI SDK, coordinated by PETi’s bounded multi-agent runtime.” Do
not claim that PETi is built on Google ADK unless a future implementation and
matching evidence actually establish that fact.

## Repository authorities reconciled

- `PETI_FULL_QUALIFICATION_BUILD_PLAN.md`
- `docs/PETI_GAP_ANALYSIS_BUILD_PLAN.md`
- `docs/HACKATHON_ARCHITECTURE.md`
- `docs/MULTI_AGENT_ARCHITECTURE.md` and related repository specifications
- `release/RC_CONFIG_FREEZE.md`
- `release/SUBMISSION_SCOPE_DECISION.md`
- `release/EXTERNAL_GATES.md`

The current local implementation, tests, release manifests, and external-gate
status are consistent with one another. Historical evidence remains labeled
historical; source-defined configuration remains distinct from externally
executed certification.

## Required follow-up before submission

If the missing external documents are supplied, rerun this reconciliation,
hash the exact files, and record any requirement-level differences. Until
then, retain the external-reference limitation and use only repository
authorities plus attached, independently verifiable evidence in submission
materials.
