# Weekly Report release decision 1.0.0

## Decision

`PENDING_EXTERNAL_CERTIFICATION` (provider narration evidence now attached)

The deterministic report core has source contracts, synthetic manifests, and a
local evaluator. This document is not a release approval.

## Local evidence

- `eval/weekly_report/dev/cases.json`
- `eval/weekly_report/held_out/cases.json`
- `eval/weekly_report/red_team/cases.json`
- `eval/weekly_report/regression/cases.json`
- `eval/weekly_report/run.py`
- `eval/weekly_report/run_gemini.py`
- `release/evidence/phase12/weekly-report-narration-real-2026-08-26.json` — Vertex Gemini held-out 7/7 pass; payloads omitted

## Required external evidence

- deterministic gates executed against the frozen release revision;
- real scheduler/dispatcher and week-boundary/DST evidence;
- real FCM/email delivery and deduplication if enabled;
- optional Gemini narration red-team/frozen-RC evidence;
- Android source deep-link and detail-screen vertical slice;
- source-traceability and no-unsupported-claim certification.
