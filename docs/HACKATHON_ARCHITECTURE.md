# PETi Hackathon Architecture

PETi is presented as a Taskmaster: one owner goal becomes a bounded, durable
plan of evidence intake, PETi Check, specialist review, safety review, and
care/report follow-up.

```text
Android / demo client
        | authenticated owner request
        v
Cloud Run API -> AgentExecutionService (bounded plan + policy)
        |              | tools validate owner, pet and capability
        |              +--> Evidence Intake -> PETi Check -> Safety Review
        v
Cloud Tasks (OIDC, private worker) -> Gemini via Vertex AI
        |                                  |
        +---------- Firestore state/result/provenance <---+
        |
        +---------- private GCS media (temporary URLs only)
        v
Android result: observations, uncertainty, limitations, provenance,
and human-review state; never diagnosis or prescription.
```

The model is a bounded provider. Application policy owns authorization,
budgets, idempotency, state transitions, and safety gates. Real Gemini and
Cloud evidence is attached to the release evidence directory only after a
sandbox run; local fake runs are never labeled as cloud certification.
