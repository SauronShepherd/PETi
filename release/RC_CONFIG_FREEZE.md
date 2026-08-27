# PETi release-candidate configuration freeze

Status: `SOURCE_CONFIG_FREEZE_DEFINED_EXTERNAL_RC_BINDING_PENDING`
Defined date: 2026-08-27

This file defines the intended configuration that all subsequent hackathon
evaluation artifacts must bind to. It does not assert that every deployed
sandbox revision has used this configuration.

| Setting | Frozen value |
|---|---|
| Environment | `DEV` / non-production sandbox |
| AI provider | `GEMINI` through the official `google-genai` SDK |
| Model | `gemini-3.5-flash` |
| Gemini location | `global` |
| Gemini transport | `SDK` |
| PETi Check | `false` until its evidence is bound to this freeze |
| Premium / Play Billing | excluded by `release/SUBMISSION_SCOPE_DECISION.md` |
| Worker ingress | internal-only |

Before submission, an operator must record the exact deployed API/worker
revision IDs, prompt/schema/guardrail hashes, feature flags, provider model
configuration, and evaluation artifact IDs in an immutable evidence record.
Until that record exists, this freeze remains source-defined rather than
externally certified.
