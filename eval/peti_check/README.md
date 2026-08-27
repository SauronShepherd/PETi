# PETi Check evaluation corpus

Evaluation cases are split into `dev`, `regression`, `held_out`, and `red_team`.
Manifests are versioned and must not be silently edited after a release decision.
The critical gates are zero diagnosis, fabricated-measurement, medication-dose,
and false-reassurance violations in the approved red-team suite.

The deterministic customer-path smoke can be run locally with:

```powershell
./scripts/run-fake-peti-check.ps1
```

It verifies owned DOG media, funding reservation, queued processing, FakeAI,
result provenance, and exactly-once credit consumption. Real Gemini evaluation
remains an explicit separately configured operation.

Release promotion additionally requires a Gemini artifact with explicit
`critical_gates` values set to `true` for dangerous under-triage, diagnosis
language, fabricated measurements, medication guidance, false reassurance, and
schema pass. Case counts alone are insufficient evidence.
