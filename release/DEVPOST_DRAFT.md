# PETi — Devpost Draft

## What it does

PETi turns an ambiguous pet-care concern into a bounded, reviewable workflow.
An owner submits synthetic or private evidence; PETi validates the evidence,
selects an appropriate specialist, runs asynchronous analysis, applies safety
review, and preserves provenance for care continuity. PETi provides observable
findings, uncertainty, limitations, and safety guidance. It does not diagnose,
prescribe, or claim that disease has been ruled out.

## Why it is agentic

PETi is a Taskmaster: the orchestrator creates a limited plan and delegates to
Evidence Intake, PETi Check, specialist analysis, Safety Review, and Care/Report
steps. Each handoff has a schema, owner/capability authorization, timeout and
durable state. Cloud Tasks delivers work to a private Cloud Run worker; Gemini
via Vertex AI is called only from the backend; Firestore stores state and
provenance; private GCS stores media with temporary access.

## Google technology

Firebase Authentication, Firestore, Cloud Storage, Cloud Tasks, Cloud
Run, Cloud Scheduler, Pub/Sub, Vertex AI, and the official Google GenAI SDK.

## Safety and privacy

Safety policy is independent of model wording. Pending extracted facts require
human review, owner isolation is enforced server-side, queued work is frozen
on deletion, and logs exclude raw media, tokens, secrets, and signed URLs.

## Current release disposition

The hackathon release is free and excludes Billing. Local verification and
sandbox deployment evidence are included in `release/evidence/`; live provider,
physical-device, production-signing, Play Console, and public-HTTPS evidence
must be attached before submission.
