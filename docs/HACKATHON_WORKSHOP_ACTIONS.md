# Hackathon workshop actions

This document translates the four official workshop themes into PETi actions.
PETi remains a Taskmaster: one owner goal becomes a bounded, asynchronous
workflow with evidence and safety review.

## Multi-Agent Teams

Use a coordinator with explicit specialist delegation. The current ADK graph
contains evidence intake, specialist review and safety review sub-agents. The
durable PETi state machine remains authoritative; ADK agents cannot choose
owners, write Firestore directly, or bypass the tool gateway.

For the demo, show the delegation and the persisted step list, not merely a
single Gemini response. The workflow is intentionally sequential because each
stage depends on the output and evidence from the preceding stage.

## Long-Running Agents

Cloud Tasks is the wake-up mechanism and Firestore is the durable checkpoint.
Runs use explicit `CREATED`, `QUEUED`, `RUNNING`, `WAITING`, `COMPLETED`,
`FAILED` and `CANCELLED` states. Retries must be idempotent and must resume
from the persisted checkpoint rather than replaying an external action.

The demo should include one queued run and one `REVIEW_REQUIRED` result to make
the background behavior visible. Do not use a blocked server thread as the
long-running mechanism.

## Self-Evolving Agents

Do not let a production pet-care agent rewrite its own safety instructions or
guardrails. That would undermine the independent safety boundary. The safe
adaptation loop is offline: collect evaluation failures and reviewer feedback,
propose a versioned prompt/policy candidate, run the held-out and red-team
evaluations, and promote only a reviewed candidate. Runtime agents consume
only the approved immutable version.

This gives PETi a credible self-improvement story without allowing metric
gaming or unsafe online self-modification.

## Agent Memory

Persistence is not automatically memory. PETi should distinguish:

1. session state: current run, checkpoint and pending context request;
2. bounded profile memory: owner-approved pet facts such as age, weight and
   recurring care preferences;
3. evidence memory: source-linked observations and provenance, retrievable by
   pet and owner; and
4. optional semantic retrieval, only when it can preserve source references
   and deletion guarantees.

For the hackathon demo, the first three levels are sufficient and safer than
adding an unbounded vector index at the last minute. Every recalled fact must
retain its source reference and owner scope.

## Last-mile demo changes

- Display the ADK graph and specialist handoff in the architecture slide.
- Show a run surviving a worker restart or retry.
- Show the agent asking for missing evidence and entering `WAITING`.
- Show the safety agent converting uncertain output to `REVIEW_REQUIRED`.
- State explicitly that self-evolution is offline and gated.
- State explicitly that PETi memory is source-grounded and owner-scoped.
