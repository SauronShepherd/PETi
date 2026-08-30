# PETi cost and environment policy

LOCAL development and pull-request verification use emulators, FakeAI, and
deterministic fixtures. Cloud environments are not invoked implicitly by local
commands.

DEV, STAGING, and PRODUCTION may use billable GCP and Gemini, and
notification services only through an explicit operator action after reviewing
the target project, budget, IAM, secrets, and release gates. Real credentials
and service-account JSON must never be committed.

Deployment paths must keep provider and model kill switches available and must
preserve ordinary metadata, existing results, export, and deletion when
variable-cost intake is disabled. External execution remains evidence-gated;
source presence alone does not certify a release.
