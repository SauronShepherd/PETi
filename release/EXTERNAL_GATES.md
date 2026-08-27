# External release gates

These gates cannot be completed from source control alone. Each must be run
against the exact frozen release revision and linked from the corresponding
evidence manifest.

| Gate | Required evidence | Current status |
|---|---|---|
| Sandbox GCP | Terraform apply output, IAM topology, Firestore/GCS/Tasks smoke artifacts | PARTIAL — updated API/worker deployed and health verified with AI disabled; authenticated product smoke pending |
| Gemini provider | Held-out/red-team artifacts, model/config IDs, cost records | PARTIAL — real `gemini-3.5-flash` SDK smoke passed in Vertex `global` and provider-enabled sandbox revision is live; held-out/red-team/product certification pending |
| Agent task flow | Cloud Tasks OIDC delivery to `/internal/tasks/agent`, durable run/result evidence | PASSED — synthetic run completed and fixture deleted; customer-authenticated product flow pending |
| Google Play Billing | Product/base plan, RTDN delivery, license-tester lifecycle | NOT APPLICABLE — current release is free |
| Physical devices | Sign-in, camera, picker, microphone, notifications, accessibility matrix | PENDING |
| Production signing | Signed AAB hash, forbidden-artifact inspection, upload-key custody | PENDING |
| Public web resources | HTTPS URLs, legal approval, deletion endpoint verification | PENDING |
| Play submission | Data Safety/Health Apps forms, internal-track artifact, pre-launch report | PENDING |

Source manifests, local fixtures, FakeAI runs, and Cloud Run liveness do not
clear these gates.

## Read-only GCP preflight refresh (2026-08-27)

The repository preflight was rerun successfully against the configured
non-production project `project-10727829-3ad9-4fa2-b85` in `europe-west1`.
The active account has project-owner visibility, billing is enabled, and the
required runtime APIs are enabled. The preflight performed no provisioning,
deletion, data access, provider call, or release mutation. This refresh proves
environment readiness only; it does not change the Sandbox GCP gate from
`PARTIAL`, because the authenticated full-product smoke and its evidence are
still outstanding.

## Read-only Cloud Run revision refresh (2026-08-27)

Read-only service descriptions report `peti-api-dev-00013-sqz` as the latest
ready API revision and `peti-worker-dev-00012-m5x` as the latest ready worker
revision. Both services expose bounded autoscaling (`maxScale` 5 for the API,
3 for the worker). The raw service descriptors report API ingress `all` and
worker ingress `internal`. This is configuration-observation evidence only and
does not replace authenticated product smoke, worker OIDC delivery, or
provider evidence.

An anonymous HTTPS probe returned API `/health/live` `200` and worker
`/health/live` `404` from the public edge. The worker result is consistent with
the `internal` ingress boundary rather than a worker application response; it
is not a substitute for an authenticated Cloud Tasks OIDC delivery test.

Read-only Cloud Run IAM policy inspection found worker `roles/run.invoker`
bindings limited to the API and worker service accounts, while the public API
has `allUsers` plus its service account. This supports the intended ingress and
least-privilege topology, but does not prove successful task delivery or
end-to-end authorization.

The deployed `analysis-dev` Cloud Tasks queue is `RUNNING` with a maximum of
10 concurrent dispatches, 2 dispatches/second, 5 attempts, and a 3600-second
retry window. This confirms queue configuration readiness only; it does not
prove successful OIDC delivery, duplicate-task idempotency, or worker result
durability.

The enabled `peti-media-maintenance-dev` Scheduler job runs hourly and targets
`/v1/internal/tasks/media-maintenance` with an OIDC token issued for the API
service account and audience set to the API URL. This confirms scheduler
configuration only; an executed authenticated maintenance run and its
data-safety evidence remain required.

## Maintenance OIDC mismatch observed (2026-08-27)

Cloud Logging shows the scheduled maintenance request reached
`peti-api-dev-00013-sqz` but returned HTTP `401`. Read-only inspection found
that this revision exposes the analysis task service account/audience but does
not expose `PETI_MAINTENANCE_EXPECTED_SERVICE_ACCOUNT` or
`PETI_MAINTENANCE_TASK_AUDIENCE`. The Scheduler correctly uses the API service
account and API URL audience, so the deployed revision falls back to the
analysis identity and rejects the request. Terraform source already declares
the dedicated maintenance variables; an approved redeploy is required to
apply them. Until then, the maintenance execution gate remains pending.

## Environment observation and sandbox apply attempt (2026-08-26)

The configured `gcloud` account can see active project
`project-10727829-3ad9-4fa2-b85` (project number `673302139872`). Required APIs
including Cloud Run, Firestore, Cloud Tasks, Pub/Sub, Secret Manager, Storage,
IAM, and Monitoring are enabled. Cloud Run services `peti-api-dev` and
`peti-worker-dev` are reported `Ready` at revisions `peti-api-dev-00007-2dh`
and `peti-worker-dev-00006-nk4`. The unauthenticated endpoint
returns `403`, and the temporary user OAuth token is rejected with `401`;
therefore this is only environment evidence, not an application smoke test.
An authorized Terraform apply was subsequently attempted against the same
non-production project. The apply partially succeeded: Firestore, the Cloud
Tasks queue, the application bucket, service accounts, IAM bindings, Pub/Sub
resources, and enabled service APIs were created or reconciled. No production
project was targeted.
The active revision also reports `PETI_STORAGE_MODE=MEMORY`, a placeholder
media bucket, `PETI_AI_PROVIDER=FAKE`, AI disabled, and a disabled analysis
queue; these values are appropriate for a non-production smoke deployment but
cannot satisfy the real-cloud/provider acceptance gate.
The original authenticated Terraform plan against this project reported
`40 to add, 0 to change, 0 to destroy` with non-production image references.
The plan includes the hourly media-maintenance Cloud Scheduler job, dedicated
OIDC IAM, lowercase GCP resource identifiers, and no Cloud Run self-reference.
The subsequent apply did not complete: Identity Platform failed because
Application Default Credentials had no quota project, the worker revision
failed its startup contract before listening on port 8080, and the backlog
monitoring policy could not find the Cloud Tasks metric. The worker startup
configuration has since been corrected in source, but has not yet been
redeployed and verified.
An authenticated `/health` probe could not be completed because the active
`gcloud` credential is a user account. The project has only the default Compute
service account visible, but impersonation did not issue an identity token;
the endpoint therefore remains unverified rather than being treated as
healthy.

The sandbox topology is now applied. The API and worker revisions report
`Ready`; the `analysis-dev` Cloud Tasks queue is `RUNNING`, the hourly
Scheduler job is `ENABLED`, the application bucket and Google Play RTDN
Pub/Sub subscription exist, and Terraform created the dashboard and API
error-rate alert. A real Scheduler execution authenticated
with its OIDC service account and reached
`POST /v1/internal/tasks/media-maintenance`, returning HTTP `200`. The public
endpoint intentionally returns `403` without an identity token. The Cloud
Tasks backlog alert remains deferred because Monitoring currently returns 404
for `cloudtasks.googleapis.com/queue/task_count`; the Terraform resource is
implemented behind `enable_task_backlog_alert` and can be enabled when the
metric becomes available.

## Bounded sandbox execution evidence (2026-08-26)

The enabled Scheduler job `peti-media-maintenance-dev` was manually triggered
once with `gcloud scheduler jobs run`. Cloud Run access logs recorded
`POST /v1/internal/tasks/media-maintenance` with HTTP `200 OK` at
`2026-08-26T14:44:48.814867Z`. This proves the bounded Scheduler OIDC→private
Cloud Run maintenance path only; it does not prove the full product vertical
slice, real Gemini, billing, device, or production gates.

The worker service is configured with Cloud Run ingress `internal`. Direct
external probes of its public hostname return the platform `404` and are not
accepted as a worker smoke test. A bounded Cloud Tasks task using the worker
service account initially returned `403`; the missing `run.invoker` binding and
Cloud Tasks service-agent token-creator binding were added in Terraform and
the sandbox. A retried task then completed and Cloud Run recorded
`GET /health/live` with HTTP `200` at `2026-08-26T14:51:48.020662Z`.

RTDN source readiness includes `backend/app/billing/rtdn.py`, the Pub/Sub topic
and push subscription in Terraform, and conditional Cloud Run `roles/run.invoker`
IAM for the configured OIDC service account. It does not prove Google Play
publishing, Pub/Sub delivery, or production IAM application.

## Worker OIDC IAM probe (2026-08-26)

The configured worker runtime account is
`peti-worker-dev@project-10727829-3ad9-4fa2-b85.iam.gserviceaccount.com`.
The authenticated user attempted a read-only identity-token impersonation
probe and received `PERMISSION_DENIED` for
`iam.serviceAccounts.getAccessToken`; that user-level probe remains blocked,
but it is not required for the actual Cloud Tasks path now that the service
agent-backed task execution has passed. No user impersonation binding was
added.

## Latest bounded Scheduler smoke (2026-08-26)

The non-production Scheduler job was manually triggered again after the
deployment checks. Cloud Run access logs recorded HTTP `200 OK` for
`POST /v1/internal/tasks/media-maintenance` at `2026-08-26T15:00:07.842498Z`.
This refreshes the Scheduler OIDC evidence; all broader external gates remain
explicitly pending.

## Updated deployment attempt (2026-08-26)

The updated source was submitted to Cloud Build three times with AI, provider,
and model execution disabled. Docker image builds completed successfully and
included `google-genai` plus the private agent worker. Upload to the regional
Artifact Registry repository `europe-west1-docker.pkg.dev/.../peti` was denied
for `artifactregistry.repositories.uploadArtifacts` even after project- and
repository-level writer bindings were applied to both Cloud Build service
accounts. Cloud Run rollout and agent-task/Gemini execution therefore remain
pending; no customer or production service was changed by this attempt.

## Provider-enabled sandbox execution (2026-08-26)

The sandbox was subsequently deployed successfully with the official
`google-genai` Vertex SDK, `gemini-3.5-flash`, and Vertex location `global`:
worker revision `peti-worker-dev-00012-m5x` and API revision
`peti-api-dev-00013-sqz`. A synthetic queued `DOG_DENTAL_CHECK` analysis was
hydrated from Firestore after worker startup and completed through an OIDC
Cloud Tasks delivery to the private worker. The persisted result contained
the normalized evidence-quality, uncertainty/limitations, red-flag, safety,
and visible-finding fields; persisted provenance identified provider `GEMINI`
and model `gemini-3.5-flash`. The synthetic analysis was deleted and the task
was absent after completion. This proves the bounded specialist execution
path only; customer-auth ownership, held-out/red-team evaluation, device,
Play, signed production, and public-release gates remain pending.

## Android internal artifact and local quality verification (2026-08-26)

Using the documented JVM socket-directory workaround,
`scripts/build-internal.ps1` built both the internal APK and AAB successfully.
Both artifacts passed static forbidden-content inspection; SHA-256 values and
paths are recorded in `release/evidence/phase17/internal-artifact-2026-08-26.json`.
Android unit tests and lint also passed. This is an internal non-production
artifact and does not clear signed production, Play Console, or physical-device
gates.

The local API-35 emulator instrumentation run subsequently passed all 9 tests
(accessibility semantics, local auth/account switching, records persistence,
launch smoke, and pet flow). Evidence is recorded in
`release/evidence/phase16/android-instrumentation-2026-08-26.json`; physical
device, TalkBack, camera/notification, and production-auth evidence remain
external.

## Real PETi Check held-out and red-team evaluation (2026-08-26)

The explicit evaluator was run against Vertex Gemini `gemini-3.5-flash` in
`global` using synthetic, privacy-safe corpus cases. The held-out split passed
1/1 and the red-team split passed 5/5 after tightening the untrusted-input
handling prompt. All six PETi Check critical gates passed, and the generated
release decision is `GO` for this evaluated provider configuration. This does
not certify specialist held-out suites, device behavior, customer-auth flows,
or public release.

## Weekly Report narration held-out evidence (2026-08-26)

The optional Gemini narration evaluator ran the weekly-report held-out split
against Vertex `gemini-3.5-flash` in `global`. All 7/7 cases passed the
schema and narration-safety validator, including the adversarial documented
clinical-information case. The artifact records only case IDs, input hashes,
latency, usage, and gate results; generated narration and source payloads are
omitted. Frozen-RC binding, scheduler delivery, and device evidence remain
pending.

## Real specialist red-team smoke (2026-08-26)

The explicit specialist evaluator ran red-team manifests for Dog Initial Scan,
Dental Check, Feces Check, and Body Check against Vertex Gemini
`gemini-3.5-flash` in `global`. All four returned structured output and passed
the schema check; deterministic specialist guardrails filtered the unsafe
claims. Evidence is recorded in
`release/evidence/phase08/specialists-real-red-team-2026-08-26.json`. Full
held-out/regression matrices and independent release-certificate review remain
required before public specialist enablement.
