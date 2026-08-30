# PETi source-document reconciliation

Status: `SOURCE_RECONCILIATION_COMPLETE_EXTERNAL_REFERENCE_SET_UNAVAILABLE`
Date: 2026-08-29

## Scope

The repository was audited against the external document paths named in the
project request. Those files are not present in the current workspace and
could not be independently read or hashed. This record therefore reconciles
the authoritative documents available in this repository and explicitly lists
the unresolved external-reference limitation.

## Architecture clarification

The repository implementation uses the official `google-genai` SDK for the
Gemini provider (`backend/app/ai/providers/`) and also contains a Google ADK
graph in `backend/app/agent_runtime/adk_graph.py`. That graph defines a PETi
coordinator plus Evidence, Specialist and Safety subagents and is covered by
`backend/tests/test_adk_graph.py`. The bounded PETi state machine remains the
application safety/orchestration boundary.

This proves local ADK composition, not yet a deployed authenticated `run_async`
execution with durable ADK event/checkpoint mapping. Submission language may
state that PETi uses Google Gemini via the official GenAI SDK and a Google ADK
coordinator with Evidence, Specialist and Safety subagents; deployed execution
and its evidence remain an external release gate.

## Repository authorities reconciled

- `docs/FINAL_HACKATHON_READINESS_AUDIT_2026-08-29.md`
- `docs/NAVIGATION_UI_UX_EVIDENCE_REPORT_2026-08-29.md`
- `release/REQUIREMENTS_TRACEABILITY_MATRIX.md`
- `backend/app/agent_runtime/adk_graph.py` and its tests
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
