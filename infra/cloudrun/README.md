# Cloud Run / Cloud Tasks deployment contract

## Deployment safety

Local development remains emulator/FakeAI based. The deployment script is an
explicit operator action for a configured project and may create billable GCP
resources; run the read-only preflight and review the target project first.
Production credentials, secret values, and project-specific Firebase files must
remain outside source control.

Phase 4 uses two services:

- `peti-api`: public Cloud Run service; customer Firebase authentication.
- `peti-worker`: private Cloud Run service; only the dedicated Cloud Tasks
  caller service account may invoke `/internal/tasks/analysis`.

The worker must not be made public. Task requests use OIDC with the worker URL as
audience. The API and worker use the same package but separate container images
and entry points.

Required deployment variables:

`PETI_PROJECT_ID`, `PETI_TASKS_LOCATION`, `PETI_ANALYSIS_QUEUE_NAME`,
`PETI_ANALYSIS_WORKER_URL`, `PETI_ANALYSIS_TASK_SERVICE_ACCOUNT`,
`PETI_ANALYSIS_TASK_AUDIENCE`, `PETI_MAINTENANCE_EXPECTED_SERVICE_ACCOUNT`,
`PETI_MAINTENANCE_TASK_AUDIENCE`, `PETI_FIREBASE_PROJECT_ID`,
`PETI_MEDIA_BUCKET`.

The commands below are intentionally explicit and bounded; production deployment
requires an operator with GCP credentials.

For a validated, environment-scoped deployment, run from the repository root:

```powershell
./infra/cloudrun/deploy.ps1 -Environment dev
```

Run the read-only prerequisite check first:

```powershell
./infra/cloudrun/preflight.ps1
```

The script validates all required variables, creates the bounded queue if absent,
deploys the worker privately, grants invocation only to the task service account,
then deploys the public API. The API receives a separate maintenance task
identity/audience so Scheduler requests cannot fall back to analysis-worker
credentials. PETi Check is disabled by default in the deployment script until
evaluation evidence is approved.

AI kill switches can be controlled without a client release, for example:

```powershell
./infra/cloudrun/deploy.ps1 -Environment dev -ProviderEnabled:$false
```

The release configuration also requires operator-provided advertising and
rewarded-unit IDs; debug/internal variants use Google test IDs.

`cloudbuild.yaml` builds and pushes distinct API and worker images; the worker
image uses `app.main_worker:app` as its container command.

Images are stored in the regional Artifact Registry repository `peti` using
`<region>-docker.pkg.dev/<project>/peti`. The deployment script creates that
repository idempotently in the selected non-production project.

The equivalent `gcloud` provisioning commands are intentionally kept in the
deployment script so the operator has one auditable path. Use local emulators
and FakeAI for development; use real provider flags only after evaluation and
budget approval.
`queue.yaml.template` is the deploy-time queue configuration template. Render
it from the environment variables before using it with `gcloud`; no service
account, worker URL, project ID, or secret is committed to the repository.
Use `scripts\render-cloud-config.ps1` to render it. The generated file is
ignored and must not be committed.
